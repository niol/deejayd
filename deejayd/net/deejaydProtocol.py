from twisted.application import service, internet
from twisted.internet import protocol
from twisted.internet.error import ConnectionDone
from twisted.protocols.basic import LineReceiver
from deejayd.net.commands import *
from deejayd.ui.config import DeejaydConfig
from xml.dom import minidom

class DeejaydProtocol(LineReceiver):

    def __init__(self):
        self.delimiter = "\n"
        self.MAX_LENGTH = 4096
        self.mpdCompatibility = DeejaydConfig().get("net", "mpd_compatibility")
        self.lineProtocol = True

    def connectionMade(self):
        self.cmdFactory = CommandFactory()
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
            self.delimiter = "</deejayd>\n"
            self.transport.write("OK\n")
            return

        if not self.lineProtocol:
            remoteCmd = self.cmdFactory.createCmdFromXML(line)
        else:
            remoteCmd = self.cmdFactory.createCmd(line)
        self.transport.write(remoteCmd.execute())

    def lineLengthExceeded(self, line):
        self.transport.write("ACK line too long\n")
        self.transport.loseConnection()
        

class DeejaydFactory(protocol.ServerFactory):
    protocol = DeejaydProtocol

    def stopFactory(self):
        djDB.close()
        djMediaSource.close()


class CommandFactory:

    def __init__(self):
        self.beginList = False
        self.queueCmdClass = None

   # XML Commands
    def createCmdFromXML(self,line):
        try: xmldoc = minidom.parseString(line)
        except: 
            return commandsXML.Error("Unable to parse the XML command")

        queueCmd = commandsXML.queueCommands()
        cmds = xmldoc.getElementsByTagName("command")

        for cmd in cmds: 
            (cmdName,cmdClass,args) = parseXMLCommand(cmd)
            queueCmd.addCommand(cmdName,cmdClass,args)

        return queueCmd

    def parseXMLCommand(self,cmd):
        cmdName = cmd.getAttribute("name") 
        args = {}
        for arg in cmd.getElementsByTagName("arg"):
            name = arg.attributes["name"].value
            value = arg.firstChild.data
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
                            "setvolume":commandsXML.Volume,
                            "seek":commandsXML.Seek,
                            "random":commandsXML.Random,
                            "repeat":commandsXML.Repeat,
                        # Playlist commands
                            "playlistInfo":commandsXML.PlaylistInfo,
                            "playlistList":commandsXML.PlaylistList,
                            "playlistAdd":commandsXML.PlaylistAdd,
                            "playlistDel":commandsXML.PlaylistDel,
                            "playlistClear":commandsXML.PlaylistClear,
                            "playlistMove":commandsXML.PlaylistMove,
                            "playlistShuffle":commandsXML.PlaylistShuffle,
                            "playlistRemove":commandsXML.PlaylistRemove,
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
    def createCmd(self, rawCmd):

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
            self.queueCmdClass = queueCommands(cmdName,self)
            self.beginList = True
            return self.queueCmdClass
        elif cmdName == 'setmode':
            mode = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or None
            return Mode(cmdName,mode)
        elif cmdName == 'status':
            return Status(cmdName)
        elif cmdName == 'stats':
            return Stats(cmdName)
        elif cmdName == 'ping':
            return Ping(cmdName)
        # MediaDB Commands
        elif cmdName == 'update':
            dir = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or ""
            return UpdateDB(cmdName,dir)
        elif cmdName == 'lsinfo':
            dir = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or ""
            return Lsinfo(cmdName,dir)
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
            return Search(cmdName,type,content)
        # Playlist Commands
        elif cmdName == 'pllist':
            return PlaylistList(cmdName)
        elif cmdName == 'add':
            path = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or ""
            return AddPlaylist(cmdName,path)
        elif cmdName in ('playlist','playlistinfo','currentsong'):
            playlisName = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or None
            return GetPlaylist(cmdName,playlisName)
        elif cmdName == 'clear':
            return ClearPlaylist(cmdName)
        elif cmdName == 'shuffle':
            return ShufflePlaylist(cmdName)
        elif cmdName in ('delete','deleteid'):
            nb = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or None
            return DeletePlaylist(cmdName,nb)
        elif cmdName in ('move','moveid'):
            (id,newPos) = (None,None) 
            if len(splittedCmd) == 2:
                numbers = splittedCmd[1].split(" ",1)
                if len(numbers) == 2: (id,newPos) = (numbers[0],numbers[1])
            return MoveInPlaylist(cmdName,id,newPos)
        elif cmdName in ('load','save','rm'):
            playlisName = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or None
            return PlaylistCommands(cmdName,playlisName)
        # Player Commands
        elif cmdName in ('stop','pause','next','previous'):
            return SimplePlayerCommands(cmdName)
        elif cmdName in ('play','playid'):
            nb = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or -1
            return PlayCommands(cmdName,nb)
        elif cmdName == 'setvol':
            vol = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or ""
            return SetVolume(cmdName,vol)
        elif cmdName == "seek":
            t = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or -1
            return Seek(cmdName,t)
        elif cmdName in ('repeat','random'):
            v = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or None
            return PlayerMode(cmdName,v)
        else:
            return UnknownCommand(cmdName)


# vim: ts=4 sw=4 expandtab
