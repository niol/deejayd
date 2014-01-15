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


class DeejaydMainHandler(Resource):

    def __init__(self):
        Resource.__init__(self)
        self.putChild("m", DeejaydMobileRessource())
        self.putChild("webui", DeejaydDesktopRessource())

    def getChild(self, name, request):
        if name == '': return self
        return Resource.getChild(self,name,request)

    def render_GET(self, request):
        user_agent = request.getHeader("user-agent");
        root = request.prepath[-1] != '' and request.path + '/' or request.path
        # if user_agent.lower().find("mobile") != -1:
        #     # redirect to specific mobile interface
        #     request.redirect(root + 'm/')
        #     return 'redirected'
        # else: # default web interface
        #     request.redirect(root + 'webui/')
        #     return 'redirected'
        request.redirect(root + 'webui/')
        return 'redirected'


class _DeejaydUIResource(Resource):
    tpl = ''
    scripts = []

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

        return self._build()

    def _load_script(self, script, type="text/javascript"):
        return "<script type='%(t)s' src='%(src)s'></script>" % {
            "t": type,
            "src": script,
            }

    def _djdscripts(self, config):
        return "\n".join(map(lambda s: self._load_script(s[0], s[1]),
                             self.scripts))

    def _i18n_dict(self, config):
        return json.dumps({
            "hours": _("Hours"),
            "minutes": _("Minutes"),
            "seconds": _("Seconds"),
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
            "seek_dialog_title": _("Seek dialog"),
            "seek": _("Seek"),
            "video_options": _("Video Options"),
            "audio_video_offset": _("Audio/Video offset"),
            "sub_offset": _("Audio/Subtitle offset"),
            "audio_channels": _("Audio channels"),
            "sub_channels": _("Subtitle channels"),
        })

    def _get_page_args(self):
        config = DeejaydConfig()
        return {
            "root_url": config.get("webui", "root_url"),
            "custom_scripts": self._djdscripts(config),
            "i18n_dict": self._i18n_dict(config),
            "close": _("Close"),
        }

    def _build(self):
        tpl_path = os.path.join(os.path.dirname(__file__), self.tpl)
        tpl_content = ""
        with open(tpl_path) as tpl:
            tpl_content = tpl.read()
        page_content = tpl_content % self._get_page_args()
        return page_content.encode("utf-8")


class DeejaydDesktopRessource(_DeejaydUIResource):
    tpl = 'desktop.thtml'
    scripts = [
        ("../gen/djd_desktop.js", "text/javascript"),
        ]

class DeejaydMobileRessource(_DeejaydUIResource):
    tpl = 'mobile.thtml'
    scripts = [
        ("../gen/djd_mobile.js", "text/javascript"),
        ]

    def _get_page_args(self):
        args = _DeejaydUIResource._get_page_args(self)
        args.update({
            "loading": _("Loading..."),
            "music": _("Music"),
            "video": _("Video"),
            "webradio": _("Webradio"),
            "genre": _("Genre"),
            "artist": _("Artist"),
            "album": _("Album"),
            "folder": _("Folder"),
            "repeat": _("Repeat"),
        })

        return args


# vim: ts=4 sw=4 expandtab
