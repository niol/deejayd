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
    equals_tags = ('genre','artist','album')
    contains_tags = ('genre','artist','album','title','all')
    #default_orders = [("album", "ascending"), ("tracknumber", "ascending")]
    default_orders = ["album", "tracknumber"]

    def __init__(self, db, library):
        super(PanelSource, self).__init__(db, library)

        # get recorded panel medialist
        filter = And()
        try: ml_id = self.db.get_medialist_id(self.base_medialist, 'magic')
        except ValueError: # medialist does not exist
            pass
        else:
            filter.filterlist = self.db.get_magic_medialist_filters(ml_id)
        self.__filters_to_parms(filter)

        # custom attributes
        self.__selected_mode = {
            "type": self.db.get_state("panel-type"),
            "value": self.db.get_state("panel-value")}
        self.__orders = self.__class__.default_orders
        self.__update_active_list(self.__selected_mode["type"],\
            self.__selected_mode["value"])

    def __filters_to_parms(self, filter = None):
        # filter as AND(Search, Panel) with
        #  * Panel : And(OR(genre=value1, genre=value2), OR(artist=value1)...)
        #  * Search : OR(tag1 CONTAINS value, )
        self.__search, self.__panel, self.__filter = None, {}, filter
        if filter != None:
            for ft in filter.filterlist:
                if ft.get_name() == "and": # panel
                    for panel_ft in ft.filterlist:
                        tag = panel_ft.filterlist[0].tag
                        self.__panel[tag] = panel_ft
                elif ft.get_name() == "or" or ft.type == "basic": # search
                    self.__search = ft

    def __update_panel_filters(self):
        # rebuild filter
        self.__filter = And()
        if self.__search:
            self.__filter.filterlist.append(self.__search)
        panel_filter = And()
        panel_filter.filterlist = self.__panel.values()
        self.__filter.filterlist.append(panel_filter)

        medias = self.library.search(self.__filter, self.__orders)
        self._media_list.set(medias)
        self.dispatch_signame(self.__class__.source_signal)

    def __update_active_list(self, type, pl_id):
        if type == "playlist":
            try: medias = self._get_playlist_content(pl_id)
            except SourceError: # playlist does not exist, set to panel
                self.__selected_mode["type"] = "panel";
                medias = self.library.search(self.__filter, self.__orders)
        elif type == "panel":
            medias = self.library.search(self.__filter, self.__orders)
        else:
            raise TypeError
        self._media_list.set(medias)

    def set_panel_filters(self, tag, values):
        if tag not in self.__class__.equals_tags:
            raise SourceError(_("Tag %s not supported") % tag)
        if not values:
            self.remove_panel_filters(tag)
            return
        filter = Or()
        for value in values:
            filter.combine(Equals(tag, value))
        self.__panel[tag] = filter
        self.__update_panel_filters()

    def remove_panel_filters(self, tag):
        try: del self.__panel[tag]
        except KeyError:
            pass
        self.__update_panel_filters()

    def clear_panel_filters(self):
        self.__panel = {}
        self.__update_panel_filters()

    def set_search_filter(self, tag, value):
        if tag not in self.__class__.contains_tags:
            raise SourceError(_("Tag %s not supported") % tag)
        if tag == "all":
            new_filter = Or()
            for tg in ('title','genre','artist','album'):
                new_filter.combine(Contains(tg, value))
        else:
            new_filter = Contains(tag, value)
        self.__search = new_filter
        self.__panel = {} # remove old panel filter
        self.__update_panel_filters()

    def clear_search_filter(self):
        if self.__search:
            self.__search = None
            self.__update_panel_filters()

    def set_orders(self, orders):
        pass

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
            return self._media_list.get(start, stop), self.__filter,\
                    self.__orders
        elif self.__selected_mode["type"] == "playlist":
            return self._media_list.get(start, stop), None, None

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
        filter_list = self.__filter.filterlist
        self.db.set_magic_medialist_filters(self.base_medialist, filter_list)

# vim: ts=4 sw=4 expandtab
