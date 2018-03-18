# Deejayd, a media player daemon
# Copyright (C) 2007-2017 Mickael Royer <mickael.royer@gmail.com>
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
from twisted.web import static, server
from twisted.web.resource import Resource, NoResource
from deejayd import DeejaydError
from deejayd.ui import log
from txsockjs.factory import SockJSResource
from deejayd.server.protocol import DeejaydFactory
from deejayd.webui.webui import DeejaydMainHandler


class DeejaydWebError(DeejaydError):
    pass


class DeejaydRootRedirector(Resource):

    def __init__(self, root_url, webui_handler):
        Resource.__init__(self)

        self.root_url = root_url.encode("utf-8")
        self.webui_handler = webui_handler

    def getChild(self, name, request):
        if name == b'' or name == b'/':
            return self

        prepath = b'/%s/' % b'/'.join(request.prepath)
        if prepath.startswith(self.root_url):
            # In webui
            return self.webui_handler
        elif request.path.startswith(self.root_url):
            # Right path to the webui
            return self
        else:
            return NoResource()

    def render_GET(self, request):
        if request.path == b'/':
            request.redirect(self.root_url)
            return b'redirected'


class SiteWithCustomLogging(server.Site):

    def _openLogFile(self, path):
        self.log_file = log.LogFile(path, mode="ab", buffering=0)
        return self.log_file.fd

    def reopen_log(self):
        self.log_file.reopen()
        # Change the logfile fd from HTTPFactory internals.
        self.logFile = self.log_file.fd


def init(deejayd_core, config, webui_logfile, htdocs_dir):
    # main handler
    main_handler = DeejaydMainHandler()
    # json-rpc handler
    main_handler.putChild("rpc", SockJSResource(DeejaydFactory(deejayd_core)))

    for d in ('dist', 'ressources'):
        path = os.path.join(htdocs_dir, d)
        main_handler.putChild(d, static.File(path))

    root_url = config.get('webui', 'root_url')
    root_url = root_url[-1] == '/' and root_url or root_url + '/'
    if root_url == '/':
        root = main_handler
    else:
        root = DeejaydRootRedirector(root_url, main_handler)

    return SiteWithCustomLogging(root, logPath=webui_logfile)
