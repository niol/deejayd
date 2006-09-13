#!/usr/bin/env python
"""
This is the file used to launch the application
ex : twistd -r glib2 -noy deejayd.tac
"""

from twisted.application import service, internet
from deejayd.net.deejaydProtocol import DeejaydFactory
from deejayd.ui.config import DeejaydConfig

# Init random generator
import random
random.seed()


application = service.Application("deejayd")
factory = DeejaydFactory()

port = DeejaydConfig().getint("net", "port")
internet.TCPServer(port, factory).setServiceParent(
    service.IServiceCollection(application))

# vim: ts=4 sw=4 expandtab
