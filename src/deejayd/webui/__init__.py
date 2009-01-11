# Deejayd, a media player daemon
# Copyright (C) 2007-2008 Mickael Royer <mickael.royer@gmail.com>
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
from deejayd.ui.log import LogFile

# xul parts
from deejayd.webui.xul import build as xul_build
from deejayd.webui.xul import xmlanswer as xul_xmlanswer
from deejayd.webui.xul import commands as xul_commands

# mobile parts
from deejayd.webui import mobile
from deejayd.webui.mobile import xmlanswer as mobile_xmlanswer
from deejayd.webui.mobile import commands as mobile_commands

class DeejaydWebError(DeejaydError): pass

class DeejaydXulHandler(Resource):

    def __init__(self, deejayd, config):
        Resource.__init__(self)
        self.__deejayd = deejayd
        self.__config = config

    def getChild(self, name, request):
        if name == '': return self
        return Resource.getChild(self,name,request)

    def render_GET(self, request):
        request.setHeader("Content-Type", "application/vnd.mozilla.xul+xml")
        return xul_build(self.__config)


class DeejaydMobileHandler(Resource):

    def __init__(self, deejayd, config):
        Resource.__init__(self)
        self.__deejayd = deejayd
        self.__config = config

    def getChild(self, name, request):
        if name == '': return self
        return Resource.getChild(self,name,request)

    def render_GET(self, request):
        try: rs = mobile.build_template(request.getHeader("user-agent"))
        except IOError, err:
            raise DeejaydWebError(err)
        return rs


class _DeejaydCommandHandler(Resource):
    isLeaf = True

    def __init__(self, deejayd, tmp_dir):
        Resource.__init__(self)
        self._deejayd = deejayd
        self._tmp_dir = tmp_dir

    def render_GET(self,request):
        return self._render(request,"get")

    def render_POST(self,request):
        return self._render(request,"post")

    def _render(self, request, type):
        raise NotImplementedError


class DeejaydXulCommandHandler(_DeejaydCommandHandler):

    def _render(self, request, type):
        # init xml answer
        request.setHeader("Content-type","text/xml")
        ans = xul_xmlanswer.DeejaydWebAnswer(self._tmp_dir)

        try: action = request.args["action"]
        except KeyError:
            ans.set_error(_("You have to enter an action."))
            return ans.to_xml()
        try: cmd_cls = xul_commands.commands[action[0]]
        except KeyError:
            ans.set_error(_("Command %s not found") % action[0])
            return ans.to_xml()

        if cmd_cls.method != type:
            ans.set_error(_("Command send with invalid method"))
        else:
            cmd = cmd_cls(self._deejayd,ans)
            try:
                cmd.argument_validation(request.args)
                cmd.execute()
                cmd.default_result()
            except DeejaydError, err:
                ans.set_error("%s" % err)
            except commands.ArgError, err:
                ans.set_error(_("Bad argument : %s") % err)

        return ans.to_xml()


class DeejaydMobileCommandHandler(_DeejaydCommandHandler):

    def _render(self, request, type):
        request.setHeader("Content-type","text/xml")
        ans = mobile_xmlanswer.DeejaydWebAnswer(self._deejayd, self._tmp_dir)

        try: action = request.args["action"]
        except KeyError:
            ans.set_error(_("You have to enter an action."))
            return ans.to_xml()
        try:
            cmd_cls = mobile_commands.commands[action[0]]
            cmd = cmd_cls(self._deejayd, ans)
        except KeyError:
            ans.set_error(_("Command %s not found") % action[0])
            return ans.to_xml()

        if cmd_cls.method != type:
            ans.set_error(_("Command send with invalid method"))
        else:
            try:
                cmd.argument_validation(request.args)
                cmd.execute()
                cmd.set_answer()
            except DeejaydError, err:
                ans.set_error("%s" % err)
            except commands.ArgError, err:
                ans.set_error(_("Bad argument : %s") % err)

        return ans.to_xml()


class SiteWithCustomLogging(server.Site):

    def _openLogFile(self, path):
        self.log_file = LogFile(path, False)
        self.log_file.set_reopen_signal(callback=self.__reopen_cb)
        return self.log_file.fd

    def __reopen_cb(self, signal, frame):
        self.log_file.reopen()
        # Change the logfile fd from HTTPFactory internals.
        self.logFile = self.log_file.fd


def init(deejayd_core, config, webui_logfile):
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
    # get htdocs directory
    htdocs_dir = config.get("webui","htdocs_dir")
    if not os.path.isdir(htdocs_dir):
        raise DeejaydWebError(_("Htdocs directory %s does not exists") % \
                htdocs_dir)

    # main (xul) part
    xul_handler = DeejaydXulHandler(deejayd_core, config)
    xul_handler.putChild("commands",DeejaydXulCommandHandler(deejayd_core,\
            tmp_dir))
    xul_handler.putChild("static",static.File(htdocs_dir))
    xul_handler.putChild("rdf",static.File(tmp_dir))

    # mobile part
    if config.getboolean("webui","mobile_ui"):
        mobile_handler = DeejaydMobileHandler(deejayd_core, config)
        mobile_handler.putChild("commands",DeejaydMobileCommandHandler(\
                deejayd_core, tmp_dir))
        mobile_handler.putChild("static",static.File(htdocs_dir))
        mobile_handler.putChild("tmp",static.File(tmp_dir))
        xul_handler.putChild("m", mobile_handler)

    return SiteWithCustomLogging(xul_handler, logPath=webui_logfile)

# vim: ts=4 sw=4 expandtab
