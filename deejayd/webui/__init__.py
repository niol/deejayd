# Deejayd, a media player daemon
# Copyright (C) 2007-2009 Mickael Royer <mickael.royer@gmail.com>
#                         Alexandre Rossi <alexandre.rossi@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os
from twisted.web import static,server
from twisted.web.resource import Resource, NoResource

from deejayd import DeejaydError
from deejayd.ui import log

from txsockjs.factory import SockJSResource
from deejayd.net.protocol import DeejaydFactory
from deejayd.webui.webui import DeejaydMainResource


class DeejaydWebError(DeejaydError): pass


class DeejaydRootRedirector(Resource):

    def __init__(self, root_url, webui_handler):
        Resource.__init__(self)

        self.root_url = root_url
        self.webui_handler = webui_handler

    def getChild(self, name, request):
        if name == '': return self

        prepath = '/%s/' % '/'.join(request.prepath)
        if prepath.startswith(self.root_url):
            # In webui
            return self.webui_handler
        elif request.path.startswith(self.root_url):
            # Right path to the webui
            return self
        else:
            return NoResource()

    def render_GET(self, request):
        if request.path == '/':
            request.redirect(self.root_url)
            return 'redirected'


class SiteWithCustomLogging(server.Site):

    def _openLogFile(self, path):
        self.log_file = log.LogFile(path, False)
        self.log_file.set_reopen_signal(callback=self.__reopen_cb)
        return self.log_file.fd

    def __reopen_cb(self, signal, frame):
        self.log_file.reopen()
        # Change the logfile fd from HTTPFactory internals.
        self.logFile = self.log_file.fd


def init(deejayd_core, config, webui_logfile, htdocs_dir):
    # main handler
    main_handler = DeejaydMainResource()
    # json-rpc handler
    main_handler.putChild("rpc", SockJSResource(DeejaydFactory(deejayd_core)))
    # cover folder
    cover_folder = config.get("mediadb", "cover_directory")
    main_handler.putChild("covers", static.File(cover_folder))

    static_dir = os.path.join(htdocs_dir, 'static')
    main_handler.putChild('static', static.File(static_dir))
    gen_dir = os.path.join(htdocs_dir, 'gen')
    main_handler.putChild('gen', static.File(gen_dir))

    root_url = config.get('webui', 'root_url')
    root_url = root_url[-1] == '/' and root_url or root_url + '/'
    if root_url == '/':
        root = main_handler
    else:
        root = DeejaydRootRedirector(root_url, main_handler)

    return SiteWithCustomLogging(root, logPath=webui_logfile)


# vim: ts=4 sw=4 expandtab
