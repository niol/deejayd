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

from deejayd.mediafilters import *
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

    def __set_panel_filters(self, filters):
        self.__panel_filters = filters
        medias = self.library.search(self.__panel_filters)
        self._media_list.set(medias)
        self.dispatch_signame(self.__class__.source_signal)

    def update_panel_filters(self, tag, type, value):
        try: filter_list = self.__panel_filters.filterlist
        except (TypeError, AttributeError):
            self.__panel_filters = And()
            filter_list = []
        if type == "equals":
            found = False
            for ft in filter_list:
                if ft.get_name() == "equals" and ft.tag == tag:
                    ft.pattern = value
                    found = True
                    break
            if not found: self.__panel_filters.combine(Equals(tag, value))
        elif type == "contains":
            pass # TODO
        elif type == "order":
            pass # TODO
        else:
            raise TypeError
        self.__set_panel_filters(self.__panel_filters)

    def remove_panel_filters(self, type, tag):
        if not self.__panel_filters: return
        if type == "equals":
            for ft in self.__panel_filters.filterlist:
                if ft.get_name() == "equals" and ft.tag == tag:
                    self.__panel_filters.filterlist.remove(ft)
                    self.__set_panel_filters(self.__panel_filters)
                    return

    def clear_panel_filters(self):
        self.__set_panel_filters(None)

    def get_active_list(self):
        return self.__selected_mode

    def set_active_list(self, type, plname):
        if type == self.__selected_mode["type"]\
                and plname == self.__selected_mode["value"]:
            return # we do not need to update panel
        if type == "playlist":
            self._media_list.set(self._get_playlist_content(plname))
            value = plname
        elif type == "panel":
            medias = self.library.search(self.__panel_filters)
            self._media_list.set(medias)
            value = ""
        else:
            raise TypeError
        self.__selected_mode = {"type": type, "value": plname}
        self.dispatch_signame(self.__class__.source_signal)

    def get_content(self, start = 0, stop = None):
        return self._media_list.get(start, stop), self.__panel_filters

    def close(self):
        states = [
            (self._playorder.name, self.name+"-playorder"),
            (str(self._media_list.list_id),self.__class__.name+"id"),
            (self.__selected_mode["type"],"panelmode-type"),
            (self.__selected_mode["value"],"panelmode-value"),
            ]
        if self.has_repeat:
            states.append((self._media_list.repeat, self.name+"-repeat"))
        self.db.set_state(states)

# vim: ts=4 sw=4 expandtab
