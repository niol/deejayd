# Deejayd, a media player daemon
# Copyright (C) 2007-2013 Mickael Royer <mickael.royer@gmail.com>
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

from twisted.web.resource import Resource, NoResource
from deejayd.ui.config import DeejaydConfig
from deejayd.jsonrpc import json

class DeejaydMainResource(Resource):

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

        user_agent = request.getHeader("user-agent");
        mobile_client = user_agent.lower().find("mobile") != -1

        return self.__build(mobile_client=mobile_client)

    def __load_script(self, script, type="text/javascript"):
        return "<script type='%(t)s' src='%(src)s'></script>" % {
            "t": type,
            "src": script,
            }

    def __djdscripts(self, config):
        scripts = [
            ("gen/deejayd.js", "text/javascript"),
        ]
        return "\n".join(map(lambda s: self.__load_script(s[0], s[1]),
                             scripts))

    def __i18n_dict(self, config):
        return json.dumps({
            "song": _("Song"),
            "songs": _("Songs"),
            "video": _("Video"),
            "videos": _("Videos"),
            "plsTitle": _("%s %s (%s)"),
            "clear": _("Clear"),
            "shuffle": _("Shuffle"),
            "loading": _("Loading..."),
            "unknown": _("Unknown"),
            "no_media": _("No media"),
            "connection_lost": _("Connection with server has been lost"),
            "inorder": _("In order"),
            "random": _("Random"),
            "onemedia": _("One media"),
            "allCategories": _("All cats"),
        })

    def __build(self, mobile_client=False):
        config = DeejaydConfig()

        tpl_path = os.path.join(os.path.dirname(__file__), "webui.thtml")
        tpl_content = ""
        with open(tpl_path) as tpl:
            tpl_content = tpl.read()
        page_content = tpl_content % {
            "root_url": config.get("webui", "root_url"),
            "custom_scripts": self.__djdscripts(config),
            "i18n_dict": self.__i18n_dict(config),
            "loading": _("Loading..."),
            "music": _("Music"),
            "video": _("Video"),
            "webradio": _("Webradio"),
            "genre": _("Genre"),
            "artist": _("Artist"),
            "album": _("Album"),
            "folder": _("Folder"),
            "repeat": _("Repeat"),
        }
        return page_content.encode("utf-8")

# vim: ts=4 sw=4 expandtab
