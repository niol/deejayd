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

import time
from zope.interface import implements
from deejayd.webradio.IWebradioSource import IWebradioSource
from deejayd.model.webradio import WebradioFactory
from deejayd.component import PersistentStateComponent
from deejayd.component import SignalingComponent

class _BaseWebradioSource(PersistentStateComponent, SignalingComponent):
    implements(IWebradioSource)
    NAME = ""
    state_name = ""
    initial_state = {"last_modified": -1}
    signal_name = "webradio.listupdate"

    def __init__(self):
        self.source = WebradioFactory().get_source(self.NAME)
        self.load_state()

    def get_categories(self):
        return [
            {
                "name": name,
                "id": int(i),
            } for name, i in self.source.get_categories().items()
        ]

    def get_webradios(self, cat_id=None):
        return self.source.get_webradios(cat_id)

    def get_status(self):
        return {
            "last_modified": self.state["last_modified"],
            "categories_count": self.source.get_categories_count(),
            "webradios_count": self.source.get_webradios_count(),
            }

    def get_name(self):
        return self.NAME

    def _update_state(self):
        self.state["last_modified"] += int(time.time())

    def close(self):
        PersistentStateComponent.close(self)

# vim: ts=4 sw=4 expandtab
