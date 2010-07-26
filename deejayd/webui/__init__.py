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

import os,shutil
from twisted.web import static,server
from twisted.web.resource import Resource

from deejayd.interfaces import DeejaydError
from deejayd.ui import log

# jsonrpc import
from deejayd.webui.jsonrpc import JSONRPC
from deejayd.rpc.protocol import build_protocol, set_web_subhandler

from deejayd.webui.webui import build as webui_build
from deejayd.webui.mobile import build as mobile_build


class DeejaydWebError(DeejaydError): pass

class DeejaydMainHandler(Resource):

    def getChild(self, name, request):
        if name == '': return self
        return Resource.getChild(self,name,request)

    def render_GET(self, request):
        user_agent = request.getHeader("user-agent");
        root = request.prepath[-1] != '' and request.path + '/' or request.path
        if user_agent.lower().find("mobile") != -1:
            # redirect to specific mobile interface
            request.redirect(root + 'm/')
            return 'redirected'
        else: # default web interface
            request.redirect(root + 'webui/')
            return 'redirected'

class DeejaydWebuiHandler(Resource):

    def __init__(self, config):
        Resource.__init__(self)
        self.__config = config

    def getChild(self, name, request):
        if name == '': return self
        return Resource.getChild(self,name,request)

    def render_GET(self, request):
        # Trailing slash is required for js script paths in the mobile webui,
        # therefore we need to add it if it is missing, by issuing a redirect
        # to the web browser.
        if request.prepath[-1] != '':
            request.redirect(request.path + '/')
            return 'redirected'
        return webui_build(self.__config)

class DeejaydMobileHandler(Resource):

    def __init__(self, config):
        Resource.__init__(self)
        self.__config = config

    def getChild(self, name, request):
        if name == '': return self
        return Resource.getChild(self,name,request)

    def render_GET(self, request):
        # Trailing slash is required for js script paths in the mobile webui,
        # therefore we need to add it if it is missing, by issuing a redirect
        # to the web browser.
        if request.prepath[-1] != '':
            request.redirect(request.path + '/')
            return 'redirected'
        return mobile_build(self.__config)

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
    # create tmp directory
    tmp_dir = config.get("webui","tmp_dir")
    if os.path.isdir(tmp_dir):
        try: shutil.rmtree(tmp_dir)
        except (IOError, OSError):
            raise DeejaydWebError(_("Unable to remove tmp directory %s") % \
                    tmp_dir)
    try: os.mkdir(tmp_dir)
    except IOError:
        raise DeejaydWebError(_("Unable to create tmp directory %s") % tmp_dir)

    if not os.path.isdir(htdocs_dir):
        raise DeejaydWebError(_("Htdocs directory %s does not exists") % \
                htdocs_dir)

    # main handler
    main_handler = DeejaydMainHandler()
    # json-rpc handler
    rpc_handler = JSONRPC(deejayd_core)
    rpc_handler = build_protocol(deejayd_core, rpc_handler)
    rpc_handler = set_web_subhandler(deejayd_core, tmp_dir, rpc_handler)
    main_handler.putChild("rpc",rpc_handler)
    # tmp dir
    main_handler.putChild("tmp",static.File(tmp_dir))

    # webui
    webui_handler = DeejaydWebuiHandler(config)
    webui_gwt = static.File(os.path.join(htdocs_dir,"webui", "deejayd_webui"))
    webui_handler.putChild("deejayd_webui", webui_gwt)
    webui_style = static.File(os.path.join(htdocs_dir,"webui", "style"))
    webui_handler.putChild("style", webui_style)

    main_handler.putChild("webui", webui_handler)

    # mobile part
    mobile_handler = DeejaydMobileHandler(config)
    mobile_style = static.File(os.path.join(htdocs_dir,"mobile", "style"))
    mobile_gwt = static.File(os.path.join(htdocs_dir,"mobile", "mobile_webui"))
    mobile_handler.putChild("style", mobile_style)
    mobile_handler.putChild("mobile_webui", mobile_gwt)

    main_handler.putChild("m", mobile_handler)

    return SiteWithCustomLogging(main_handler, logPath=webui_logfile)

# vim: ts=4 sw=4 expandtab
