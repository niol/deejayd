import sys
from twisted.application import service, internet
from twisted.internet import protocol
from twisted.internet.error import ConnectionDone
from twisted.protocols.basic import LineReceiver
from twisted.python import log
from xml.dom import minidom

from deejayd.ui.config import DeejaydConfig
from deejayd.mediadb import deejaydDB
from deejayd.mediadb.database import DatabaseFactory
from deejayd.sources import sources
from deejayd.player import player
from deejayd.net import commandsXML,commandsLine

class DeejaydProtocol(LineReceiver):

    def __init__(self,player,db,sources):
        self.delimiter = "\n"
        self.MAX_LENGTH = 1024
        self.lineProtocol = True
        self.deejaydArgs = {"player":player,"db":db,"sources":sources}

    def connectionMade(self):
        from deejayd import __version__
        self.cmdFactory = CommandFactory(self.deejaydArgs)
        self.transport.write("OK DEEJAYD %s\n" % (__version__,))

    def connectionLost(self, reason=ConnectionDone):
        pass

    def lineReceived(self, line):
        line = line.strip("\r")
        if line == "close":
            self.transport.loseConnection()
            return
        elif line == "setXML":
            self.lineProtocol = False
            self.MAX_LENGTH = 40960
            self.delimiter = "ENDXML\n"
            self.transport.write("OK\n")
            return

        if not self.lineProtocol:
            remoteCmd = self.cmdFactory.createCmdFromXML(line)
        else:
            remoteCmd = self.cmdFactory.createCmdFromLine(line)

        rsp = remoteCmd.execute()
        if isinstance(rsp, unicode):
            rsp = rsp.encode("utf-8")
        self.transport.write(rsp)

    def lineLengthExceeded(self, line):
        log.err("Request too long, skip it")
        self.transport.write("ACK line too long\n")
        self.transport.loseConnection()
        

class DeejaydFactory(protocol.ServerFactory):
    protocol = DeejaydProtocol
    db_supplied = False

    def __init__(self, ddb = None):
        if ddb != None:
            self.db_supplied = True
            self.db = ddb

    def startFactory(self):
        log.msg("Starting Deejayd ...")

        # Try to Init the MediaDB
        if not self.db_supplied:
            self.db = deejaydDB.DeejaydDB(DatabaseFactory().getDB(),
                            DeejaydConfig().get("mediadb","music_directory"))
        log.msg("MediaDB Initialisation...OK")

        # Try to Init the player
        try: self.player = player.deejaydPlayer(self.db)
        except player.NoSinkError:
            log.err("No audio sink found for Gstreamer, deejayd can not run")
            sys.exit("Unable to start deejayd : see log for more informations")
        log.msg("Player Initialisation...OK")

        # Try to Init sources
        self.sources = sources.sourcesFactory(self.player,self.db)
        #try: self.sources = sources.sourcesFactory(self.player,self.db)
        #except :
        #    log.err("Unable to init sources, deejayd has to quit")
        #    sys.exit("Unable to start deejayd : see log for more informations")
        log.msg("Sources Initialisation...OK")

    def stopFactory(self):
        self.player.close()
        self.sources.close()
        self.db.close()

    def buildProtocol(self, addr):
        p = self.protocol(player = self.player,
            db = self.db,sources = self.sources)
        p.factory = self
        return p


class CommandFactory:

    def __init__(self,deejaydArgs = {}):
        self.beginList = False
        self.queueCmdClass = None
        self.deejaydArgs = deejaydArgs

   # XML Commands
    def createCmdFromXML(self,line):
        try: xmldoc = minidom.parseString(line)
        except: 
            return commandsXML.Error("Unable to parse the XML command")

        queueCmd = commandsXML.queueCommands(self.deejaydArgs)
        cmds = xmldoc.getElementsByTagName("command")

        for cmd in cmds: 
            (cmdName,cmdClass,args) = self.parseXMLCommand(cmd)
            queueCmd.addCommand(cmdName,cmdClass,args)

        return queueCmd

    def parseXMLCommand(self,cmd):
        cmdName = cmd.getAttribute("name") 
        args = {}
        for arg in cmd.getElementsByTagName("arg"):
            name = arg.attributes["name"].value
            type = arg.attributes["type"].value
            if type == "simple":
                value = None
                if arg.hasChildNodes():
                    value = arg.firstChild.data
            elif type == "multiple":
                value = []
                for val in arg.getElementsByTagName("value"):
                    if arg.hasChildNodes():
                        value.append(val.firstChild.data)
            args[name] = value
            
        commandsParse = commandsXML.commandsList(commandsXML)
        if cmdName in commandsParse.keys():
            return (cmdName,commandsParse[cmdName],args)
        else: return (cmdName,commandsXML.UnknownCommand,{})


  # Line Commands
    def createCmdFromLine(self, rawCmd):
        splittedCmd = rawCmd.split(' ',1)
        cmdName = splittedCmd[0]
        try: args = splittedCmd[1]
        except: args = None

        commandsParse = commandsLine.commandsList(commandsLine)
        if cmdName in commandsParse.keys():
            return commandsParse[cmdName](cmdName,self.deejaydArgs,args)
        else:
            return commandsLine.UnknownCommand(cmdName,self.deejaydArgs,args)


# vim: ts=4 sw=4 expandtab
