import sys
from twisted.application import service, internet
from twisted.internet import protocol
from twisted.internet.error import ConnectionDone
from twisted.protocols.basic import LineReceiver
try: from xml.etree import cElementTree as ET # python 2.5
except ImportError: # python 2.4
    import cElementTree as ET


from deejayd.ui import log
from deejayd.ui.config import DeejaydConfig
from deejayd.database.database import DatabaseFactory
from deejayd.net import commandsXML
from deejayd import player,sources,mediadb

class DeejaydProtocol(LineReceiver):

    def __init__(self,db,player,audio_library,video_library,sources):
        self.delimiter = "ENDXML\n"
        self.MAX_LENGTH = 40960
        self.deejaydArgs = {"audio_library":audio_library,"player":player,\
                       "video_library":video_library,"db":db,"sources":sources,\
                       "protocol":self}

    def connectionMade(self):
        from deejayd import __version__
        self.cmdFactory = CommandFactory(self.deejaydArgs)
        self.transport.write("OK DEEJAYD %s\n" % (__version__,))

    def connectionLost(self, reason=ConnectionDone):
        pass

    def lineReceived(self, line):
        line = line.strip("\r")
        # DEBUG Informations
        log.debug(line)

        remoteCmd = self.cmdFactory.createCmdFromXML(line)
        rsp = remoteCmd.execute()
        if isinstance(rsp, unicode):
            rsp = rsp.encode("utf-8")
        # DEBUG Informations
        log.debug(rsp)

        self.transport.write(rsp + self.delimiter)
        del rsp

        if 'close' in remoteCmd.commands:
            self.transport.loseConnection()
        del remoteCmd

    def lineLengthExceeded(self, line):
        log.err("Request too long, skip it")
        self.transport.write("ACK line too long\n")
        self.transport.loseConnection()


class DeejaydFactory(protocol.ServerFactory):
    protocol = DeejaydProtocol
    obj_supplied = False

    def __init__(self, db = None, player = None, audio_library = None,\
                                                        video_library = None):
        if db != None and player != None and audio_library != None:
            self.__class__.obj_supplied = True
            self.db = db
            self.player = player
            self.audio_library = audio_library
            self.video_library = video_library

    def startFactory(self):
        config = DeejaydConfig()
        log.info("Starting Deejayd ...")

        if self.__class__.obj_supplied:
            self.sources = sources.SourceFactory(self.player,self.db,\
                               self.audio_library,self.video_library,config)
            return True

        # Init the Database
        log.info("Database Initialisation")
        self.db = DatabaseFactory(config).get_db()
        self.db.connect()

        # Init Media Backend
        log.info("Player Initialisation")
        try: self.player = player.init(self.db,config)
        except player.PlayerError, err:
            log.err(str(err))
            sys.exit(1)

        # Init audio and video library
        log.info("Libraries Initialisation")
        self.audio_library,self.video_library = mediadb.init(self.db,\
                                                             self.player,config)

        # Try to Init sources
        log.info("Sources Initialisation")
        self.sources = sources.SourceFactory(self.player,self.db,\
                                 self.audio_library,self.video_library,config)

        log.info("Deejayd started :-)")

    def stopFactory(self):
        for obj in (self.player,self.sources,self.audio_library,\
                                                  self.video_library,self.db):
            if obj != None: obj.close()

    def buildProtocol(self, addr):
        p = self.protocol(db = self.db,player = self.player,\
            audio_library = self.audio_library,\
            video_library = self.video_library,sources = self.sources)
        p.factory = self
        return p


class CommandFactory:

    def __init__(self,deejaydArgs = {}):
        self.beginList = False
        self.queueCmdClass = None
        self.deejaydArgs = deejaydArgs

   # XML Commands
    def createCmdFromXML(self,line):
        queueCmd = commandsXML.queueCommands(self.deejaydArgs)

        try: xml_tree = ET.fromstring(line)
        except:
            queueCmd.addCommand('parsing error', commandsXML.UnknownCommand, [])
        else:
            cmds = xml_tree.findall("command")
            for cmd in cmds:
                (cmdName,cmdClass,args) = self.parseXMLCommand(cmd)
                queueCmd.addCommand(cmdName,cmdClass,args)

        return queueCmd

    def parseXMLCommand(self,cmd):
        cmdName = cmd.attrib["name"]
        args = {}
        for arg in cmd.findall("arg"):
            name = arg.attrib["name"]
            type = arg.attrib["type"]
            if type == "simple":
                value = arg.text
            elif type == "multiple":
                value = []
                for val in arg.findall("value"):
                    value.append(val.text)
            args[name] = value

        if cmdName in commandsXML.commands.keys():
            return (cmdName, commandsXML.commands[cmdName], args)
        else: return (cmdName,commandsXML.UnknownCommand,{})

# vim: ts=4 sw=4 expandtab
