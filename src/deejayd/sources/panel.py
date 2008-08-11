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
from deejayd.sources._base import _BaseLibrarySource, SourceError

class PanelSource(_BaseLibrarySource):
    base_medialist = "__panelcurrent__"
    name = "panel"
    source_signal = 'panel.update'
    panel_tags = ('genre','artist','album')
    contains_tags = ('genre','artist','album','title','all')

    def __init__(self, db, library):
        super(PanelSource, self).__init__(db, library)
        try: ml_id = self.db.get_medialist_id(self.base_medialist, 'magic')
        except ValueError: # medialist does not exist
            self.__panel_filters = None
        else:
            recorded_filters = self.db.get_magic_medialist_filters(ml_id)
            self.__panel_filters = And()
            self.__panel_filters.filterlist = recorded_filters
        # custom attributes
        self.__selected_mode = {
            "type": self.db.get_state("panel-type"),
            "value": self.db.get_state("panel-value")}
        self.__update_active_list(self.__selected_mode["type"],\
            self.__selected_mode["value"])

    def __find_contains_filter(self):
        try: filter_list = self.__panel_filters.filterlist
        except (TypeError, AttributeError):
            return None
        for ft in filter_list:
            if ft.type == "basic" and ft.get_name() == "contains":
                return ft
            elif ft.type == "complex" and ft.get_name() == "or":
                return ft
        return None

    def __set_panel_filters(self, filters):
        self.__panel_filters = filters
        medias = self.library.search(self.__panel_filters)
        self._media_list.set(medias)
        self.dispatch_signame(self.__class__.source_signal)

    def __update_active_list(self, type, pl_id):
        if type == "playlist":
            try: medias = self._get_playlist_content(pl_id)
            except SourceError: # playlist does not exist, set to panel
                self.__selected_mode["type"] = "panel";
                medias = self.library.search(self.__panel_filters)
        elif type == "panel":
            medias = self.library.search(self.__panel_filters)
        else: raise TypeError
        self._media_list.set(medias)

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
            self.__panel_filters = And()
            if tag == "all":
                new_filter = Or()
                for tg in ('title','genre','artist','album'):
                    new_filter.combine(Contains(tg, value))
            else:
                new_filter = Contains(tag, value)
            self.__panel_filters.combine(new_filter)

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
        elif type == "contains":
            try: self.__panel_filters.filterlist.\
                remove(self.__find_contains_filter())
            except (TypeError, ValueError, AttributeError):
                return
        self.__set_panel_filters(self.__panel_filters)

    def clear_panel_filters(self):
        self.__set_panel_filters(None)

    def get_active_list(self):
        return self.__selected_mode

    def set_active_list(self, type, pl_id):
        if type == self.__selected_mode["type"]\
                and pl_id == self.__selected_mode["value"]:
            return # we do not need to update panel
        self.__update_active_list(type, pl_id)
        self.__selected_mode = {"type": type, "value": pl_id}
        self.dispatch_signame(self.__class__.source_signal)

    def get_content(self, start = 0, stop = None):
        if self.__selected_mode["type"] == "panel":
            return self._media_list.get(start, stop), self.__panel_filters
        elif self.__selected_mode["type"] == "playlist":
            return self._media_list.get(start, stop), None

    def close(self):
        states = [
            (self._playorder.name, self.name+"-playorder"),
            (str(self._media_list.list_id),self.__class__.name+"id"),
            (self.__selected_mode["type"],"panel-type"),
            (self.__selected_mode["value"],"panel-value"),
            ]
        if self.has_repeat:
            states.append((self._media_list.repeat, self.name+"-repeat"))
        self.db.set_state(states)
        # save panel filters
        filter_list = []
        if self.__panel_filters is not None:
            filter_list = self.__panel_filters.filterlist
        self.db.set_magic_medialist_filters(self.base_medialist, filter_list)

# vim: ts=4 sw=4 expandtab
