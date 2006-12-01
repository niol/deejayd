from twisted.application import service, internet
from twisted.internet import protocol
from twisted.internet.error import ConnectionDone
from twisted.protocols.basic import LineReceiver
from twisted.python import log
from xml.dom import minidom

from deejayd.ui.config import DeejaydConfig
from deejayd.mediadb import deejaydDB
from deejayd.sources import sources
from deejayd.player import player
from deejayd.net import commandsLine
from deejayd.net import commandsXML


class DeejaydProtocol(LineReceiver):

    def __init__(self,player,db,sources):
        self.delimiter = "\n"
        self.MAX_LENGTH = 4096
        self.lineProtocol = True
        self.deejaydArgs = {"player":player,"db":db,"sources":sources}

    def connectionMade(self):
        self.cmdFactory = CommandFactory(self.deejaydArgs)
        self.transport.write("OK DEEJAYD 0.0.1\n")

    def connectionLost(self, reason=ConnectionDone):
        pass

    def lineReceived(self, line):
        line = line.strip("\r")
        if line == "close":
            self.transport.loseConnection()
            return
        elif line == "setXML":
            self.lineProtocol = False
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
        self.transport.write("ACK line too long\n")
        self.transport.loseConnection()
        

class DeejaydFactory(protocol.ServerFactory):
    protocol = DeejaydProtocol

    def startFactory(self):
        log.msg("Startting Deejayd ...")
        # Try to Init the player
        log.msg("Player Initialisation")
        try: self.player = player.deejaydPlayer()
        except player.NoSinkError:
            log.err("No audio sink found for Gstreamer, deejayd can not run")
            from twisted.internet import glib2reactor
            glib2reactor.stop()

        # Try to Init the MediaDB
        log.msg("MediaDB Initialisation")
        self.db = deejaydDB.DeejaydDB()

        # Try to Init sources
        log.msg("Sources Initialisation")
        try: self.sources = sources.sourcesFactory(self.player,self.db)
        except:
            log.err("Unable to init sources, deejayd has to quit")
            from twisted.internet import glib2reactor
            glib2reactor.stop()

    def stopFactory(self):
        self.db.close()
        self.sources.close()

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
                value = arg.firstChild.data
            elif type == "multiple":
                value = []
                for val in arg.getElementsByTagName("value"):
                    value.append(val.firstChild.data)
            args[name] = value
            
        commandsParse = {
                        # General Commmands
                            "ping":commandsXML.Ping,
                            "status":commandsXML.Status,
                            "stats":commandsXML.Stats,
                            "mode":commandsXML.Mode,
                        # MediaDB Commmands
                            "update":commandsXML.UpdateDB,
                            "getdir":commandsXML.GetDir,
                            "search":commandsXML.Search,
                            "find":commandsXML.Search,
                        # Player commands
                            "play":commandsXML.Play,
                            "stop":commandsXML.Stop,
                            "pause":commandsXML.Pause,
                            "next":commandsXML.Next,
                            "previous":commandsXML.Previous,
                            "setVolume":commandsXML.Volume,
                            "seek":commandsXML.Seek,
                            "random":commandsXML.Random,
                            "repeat":commandsXML.Repeat,
                        # Playlist commands
                            "playlistInfo":commandsXML.PlaylistInfo,
                            "playlistCurrent":commandsXML.PlaylistCurrent,
                            "playlistList":commandsXML.PlaylistList,
                            "playlistAdd":commandsXML.PlaylistAdd,
                            "playlistRemove":commandsXML.PlaylistRemove,
                            "playlistClear":commandsXML.PlaylistClear,
                            "playlistMove":commandsXML.PlaylistMove,
                            "playlistShuffle":commandsXML.PlaylistShuffle,
                            "playlistErase":commandsXML.PlaylistErase,
                            "playlistLoad":commandsXML.PlaylistLoad,
                            "playlistSave":commandsXML.PlaylistSave,
                        # Webradios commands
                            "webradioList":commandsXML.WebradioList,
                            "webradioAdd":commandsXML.WebradioAdd,
                            "webradioDel":commandsXML.WebradioDel,
                            "webradioClear":commandsXML.WebradioClear
                        # Panel commands
                        }

        if cmdName in commandsParse.keys():
            return (cmdName,commandsParse[cmdName],args)
        else: return (cmdName,commandsXML.UnknownCommand,{})


  # Line Commands
    def createCmdFromLine(self, rawCmd):

        splittedCmd = rawCmd.split(' ',1)
        cmdName = splittedCmd[0]

        if cmdName == 'command_list_end':
            self.beginList = False
            if self.queueCmdClass:
                self.queueCmdClass.endCommand()
                return self.queueCmdClass 
            else: return UnknownCommand(cmdName)
        elif self.beginList:
            self.queueCmdClass.addCommand(rawCmd)
            return self.queueCmdClass

        if cmdName in ('command_list_begin','command_list_ok_begin'):
            self.queueCmdClass = commandsLine.queueCommands(cmdName,self)
            self.beginList = True
            return self.queueCmdClass
        elif cmdName == 'status':
            return commandsLine.Status(cmdName,self.deejaydArgs)
        elif cmdName == 'stats':
            return commandsLine.Stats(cmdName,self.deejaydArgs)
        elif cmdName == 'ping':
            return commandsLine.Ping(cmdName,self.deejaydArgs)
        # MediaDB Commands
        elif cmdName == 'update':
            dir = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or ""
            return commandsLine.UpdateDB(cmdName,self.deejaydArgs,dir)
        elif cmdName == 'lsinfo':
            dir = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or ""
            return commandsLine.Lsinfo(cmdName,self.deejaydArgs,dir)
        elif cmdName == 'search' or cmdName == 'find':
            if len(splittedCmd) == 2:
                args = splittedCmd[1].split(' ',1)
                if len(args) == 2:
                    type = args[0].strip('"')
                    content = args[1].strip('"')
                else:
                    type = ""
                    content = ""
            else:
                type = ""
                content = ""
            return commandsLine.Search(cmdName,self.deejaydArgs,type,content)
        # Playlist Commands
        elif cmdName == 'add':
            path = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or ""
            return commandsLine.AddPlaylist(cmdName,self.deejaydArgs,path)
        elif cmdName in ('playlist','playlistinfo','currentsong'):
            playlisName = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or None
            return commandsLine.GetPlaylist(cmdName,self.deejaydArgs,playlisName)
        elif cmdName == 'clear':
            return commandsLine.ClearPlaylist(cmdName,self.deejaydArgs)
        elif cmdName == 'shuffle':
            return commandsLine.ShufflePlaylist(cmdName,self.deejaydArgs)
        elif cmdName in ('delete','deleteid'):
            nb = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or None
            return commandsLine.DeletePlaylist(cmdName,self.deejaydArgs,nb)
        elif cmdName in ('move','moveid'):
            (id,newPos) = (None,None) 
            if len(splittedCmd) == 2:
                numbers = splittedCmd[1].split(" ",1)
                if len(numbers) == 2: (id,newPos) = (numbers[0],numbers[1])
            return commandsLine.MoveInPlaylist(cmdName,self.deejaydArgs,id,newPos)
        elif cmdName in ('load','save','rm'):
            playlisName = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or None
            return commandsLine.PlaylistCommands(cmdName,self.deejaydArgs,playlisName)
        # Player Commands
        elif cmdName in ('stop','pause','next','previous'):
            return commandsLine.SimplePlayerCommands(cmdName,self.deejaydArgs)
        elif cmdName in ('play','playid'):
            nb = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or -1
            return commandsLine.PlayCommands(cmdName,self.deejaydArgs,nb)
        elif cmdName == 'setvol':
            vol = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or ""
            return commandsLine.SetVolume(cmdName,self.deejaydArgs,vol)
        elif cmdName == "seek":
            t = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or -1
            return commandsLine.Seek(cmdName,self.deejaydArgs,t)
        elif cmdName in ('repeat','random'):
            v = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or None
            return commandsLine.PlayerMode(cmdName,self.deejaydArgs,v)
        else:
            return commandsLine.UnknownCommand(cmdName,self.deejaydArgs)


# vim: ts=4 sw=4 expandtab
