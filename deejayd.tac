#!/usr/bin/env python
"""
This is the file used to launch the application
ex : twistd -noy deejayd.tac
"""

from twisted.application import service, internet
from deejayd.net.deejaydProtocol import DeejaydFactory


application = service.Application("deejayd")
factory = DeejaydFactory()

internet.TCPServer(6600, factory).setServiceParent(
	service.IServiceCollection(application))

# vim: sw=8 noexpandtab
