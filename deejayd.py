from twisted.application import service, internet
from twisted.internet import protocol, reactor, defer
from twisted.protocols import basic

class deejaydProtocol(protocol.Protocol):
	pass

class deejaydFactory(protocol.ServerFactory):
	protocol = deejaydProtocol

# vim: sw=8 noexpandtab
