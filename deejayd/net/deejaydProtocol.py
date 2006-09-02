from twisted.application import service, internet
from twisted.internet import protocol, reactor, defer
from twisted.internet.error import ConnectionDone
from twisted.protocols.basic import LineReceiver
from deejayd.net.commands import *

class DeejaydProtocol(LineReceiver):

    def connectionMade(self):
        self.cmdFactory = CommandFactory()
        self.transport.write("OK DEEJAYD 0.1\n")

    def connectionLost(self, reason=ConnectionDone):
        pass

    def lineReceived(self, line):

        if line == "close":
            self.transport.loseConnection()
            return

        remoteCmd = self.cmdFactory.createCmd(line)
        if not remoteCmd.isUnknown():
            self.transport.write(remoteCmd.execute())
        else:
            self.transport.write("ACK Unknown command : %s\n" % (line,))


class DeejaydFactory(protocol.ServerFactory):
    protocol = DeejaydProtocol

    def stopFactory(self):
        djDB.close()
        djPlaylist.close()

class CommandFactory:

    def createCmd(self, rawCmd):

        splittedCmd = rawCmd.split(' ',1)
        cmdName = splittedCmd[0]

        if cmdName == 'ping':
            return Ping(cmdName)
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
        elif cmdName in ('stop','pause','next','previous'):
            return SimplePlayerCommands(cmdName)
        elif cmdName in ('play','playid'):
            nb = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or 0
            return PlayCommands(cmdName,nb)
        elif cmdName == 'add':
            path = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or ""
            return AddPlaylist(cmdName,path)
        elif cmdName == 'playlist' or cmdName == 'playlistinfo':
            return GetPlaylist(cmdName)
        elif cmdName == 'clear':
            return ClearPlaylist(cmdName)
        elif cmdName == 'setvol':
            vol = len(splittedCmd) == 2 and splittedCmd[1].strip('"') or ""
            return SetVolume(cmdName,vol)
        else:
            return UnknownCommand(cmdName)


# vim: ts=4 sw=4 expandtab
