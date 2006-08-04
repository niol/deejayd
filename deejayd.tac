#!/usr/bin/env python
"""
This is the file used to launch the application
ex : twistd -noy deejayd.tac
"""

from twisted.application import service, internet
from deejayd import deejaydFactory


application = service.Application("deejayd")
factory = deejaydFactory()

# 1079 is an example for the moment
internet.TCPServer(1079, factory).setServiceParent(
	service.IServiceCollection(application))

# vim: sw=8 noexpandtab
