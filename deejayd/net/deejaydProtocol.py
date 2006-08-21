from twisted.application import service, internet
from twisted.internet import protocol, reactor, defer
from twisted.internet.error import ConnectionDone
from twisted.protocols.basic import LineReceiver
from deejayd.net.commands import *

class DeejaydProtocol(LineReceiver):

    def connectionMade(self):
        self.cmdFactory = CommandFactory()

    def connectionLost(self, reason=ConnectionDone):
        pass

    def lineReceived(self, line):

        remoteCmd = self.cmdFactory.createCmd(line)

        if not remoteCmd.isUnknown():
            self.transport.write(remoteCmd.execute())
        else:
            self.transport.loseConnection()


class DeejaydFactory(protocol.ServerFactory):
    protocol = DeejaydProtocol


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
        else:
            return UnknownCommand(cmdName)


# vim: ts=4 sw=4 expandtab
