from twisted.application import service, internet
from twisted.internet import protocol, reactor, defer
from twisted.internet.error import ConnectionDone
from twisted.protocols.basic import LineReceiver
from deejayd.net.commands import *

class DeejaydProtocol(LineReceiver):

    def __init__(self):
        self.delimiter = "\n"
        self.MAX_LENGTH = 1024

    def connectionMade(self):
        self.cmdFactory = CommandFactory()
        self.transport.write("OK DEEJAYD 0.1\n")

    def connectionLost(self, reason=ConnectionDone):
        pass

    def lineReceived(self, line):
        line = line.strip("\r")
        if line == "close":
            self.transport.loseConnection()
            return

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
        elif cmdName == 'pladd':
            path = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or ""
            return AddPlaylist(cmdName,path)
        elif cmdName in ('playlist','playlistinfo','currentsong'):
            playlisName = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or None
            return GetPlaylist(cmdName,playlisName)
        elif cmdName == 'plclear':
            return ClearPlaylist(cmdName)
        elif cmdName == 'plshuffle':
            return ShufflePlaylist(cmdName)
        elif cmdName == 'pldelete':
            nb = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or None
            return DeletePlaylist(cmdName,nb)
        elif cmdName == 'plmove':
            (id,newPos) = (None,None) 
            if len(splittedCmd) == 2:
                numbers = splittedCmd[1].split(" ",1)
                if len(numbers) == 2: (id,newPos) = (numbers[0],numbers[1])
            return MoveInPlaylist(cmdName,id,newPos)
        elif cmdName in ('plload','plsave','plrm'):
            playlisName = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or None
            return PlaylistCommands(cmdName,playlisName)
        # Webradios Commands
        elif cmdName == 'wrlist':
            return webradioList(cmdName)
        elif cmdName == 'wrclear':
            return webradioClear(cmdName)
        elif cmdName == 'wrdel':
            nb = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or None
            return webradioErase(cmdName,nb)
        elif cmdName == "wradd":
            (url,name) = (None,None)
            if len(splittedCmd) == 2:
                args = splittedCmd[1].split(" ",1)
                if len(args) == 2: (url,name) = (args[0].strip('"'),args[1].strip('"'))
            return webradioAdd(cmdName,url,name)
        # Player Commands
        elif cmdName in ('stop','pause','next','previous'):
            return SimplePlayerCommands(cmdName)
        elif cmdName == 'play':
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
