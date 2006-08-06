from twisted.application import service, internet
from twisted.internet import protocol, reactor, defer
from twisted.internet.error import ConnectionDone
from twisted.protocols.basic import LineReceiver
from deejayd.net.commands import *

class DeejaydProtocol(LineReceiver):

	def connectionMade(self):
		self.cmdFactory = CommandFactory()
		pass

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

		splittedCmd = rawCmd.split(' ',2)
		cmdName = splittedCmd[0]

		if cmdName == 'ping':
			return Ping(cmdName)
		else:
			return UnknownCommand(cmdName)


# vim: sw=8 noexpandtab
