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
    tpl = 'webui.thtml'
    scripts = [
        ("gen/djd_app.js", "text/javascript"),
        ]

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

    def _get_page_args(self):
        config = DeejaydConfig()
        args = {
            "root_url": config.get("webui", "root_url"),
            "custom_scripts": self._djdscripts(config),
        }
        if args['root_url'][-1] != '/':
            args['root_url'] = args['root_url'] + '/'
        return args

    def _build(self):
        tpl_path = os.path.join(os.path.dirname(__file__), self.tpl)
        tpl_content = ""
        with open(tpl_path) as tpl:
            tpl_content = tpl.read()
        page_content = tpl_content % self._get_page_args()
        return page_content.encode("utf-8")

# vim: ts=4 sw=4 expandtab
