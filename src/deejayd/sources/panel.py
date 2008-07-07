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

from deejayd.sources._base import _BaseLibrarySource

class PanelSource(_BaseLibrarySource):
    base_medialist = "__panelcurrent__"
    name = "panel"
    source_signal = 'panel.update'

    def __init__(self, db, library):
        super(PanelSource, self).__init__(db, library)
        # load saved
        ans = self.db.get_static_medialist(self.base_medialist,\
            infos = library.media_attr)
        self._media_list.set(ans)
        # custom attributes
        self.__selected_mode = {"type": "panel", "value": ""}
        self.__panel_filters = None

    def set_panel_filters(self, filters):
        self.__panel_filters = filters
        self.dispatch_signame(self.__class__.source_signal)

    def get_active_list(self):
        return self.__selected_mode

    def set_active_list(self, type, plname):
        if type == "static-pl":
            value = plname
        elif type == "magic-pl":
            value = plname
        elif type == "panel":
            value = ""
        else:
            raise TypeError
        self.__selected_mode = {"type": type, "value": ""}
        self.dispatch_signame(self.__class__.source_signal)

    def get_content(self, start = 0, stop = None):
        return self._media_list.get(start, stop)

# vim: ts=4 sw=4 expandtab
