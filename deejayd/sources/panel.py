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

from deejayd.mediafilters import *
from deejayd.sources._base import _BaseSortedLibSource, SourceError
from deejayd.ui import log

class PanelSource(_BaseSortedLibSource):
    SUBSCRIPTIONS = {
            "playlist.update": "cb_playlist_update",
            "playlist.listupdate": "cb_playlist_listupdate",
            "mediadb.mupdate": "cb_library_changes",
            }
    base_medialist = "__panelcurrent__"
    name = "panel"
    source_signal = 'panel.update'
    supported_panel_tags = [\
            ['genre','artist','album'],\
            ['genre','various_artist','album'],\
            ['artist','album'],\
            ['various_artist','album'],\
            ]
    contains_tags = ('genre','artist','album','title','all')
    sort_tags = ('genre','artist','album','title','rating','tracknumber')
    default_sorts = [("album", "ascending"), ("discnumber", "ascending"), \
            ("tracknumber", "ascending")]

    def __init__(self, db, library, config):
        super(PanelSource, self).__init__(db, library)

        # get panel tags
        self.__panel_tags = config.getlist("panel", "panel_tags")
        if self.__panel_tags not in self.supported_panel_tags:
            log.err(_("You choose wrong panel tags, fallback to default"))
            self.__panel_tags = ['genre','artist','album']

        # get recorded panel medialist
        filter = And()
        try: ml_id = self.db.get_medialist_id(self.base_medialist, 'magic')
        except ValueError: # medialist does not exist
            self._sorts = []
        else:
            # get filters
            filter.filterlist = self.db.get_magic_medialist_filters(ml_id)
            # get recorded sorts
            self._sorts = list(self.db.get_magic_medialist_sorts(ml_id)) or []
        self.__filters_to_parms(filter)

        # custom attributes
        self.__selected_mode = {
            "type": self.db.get_state("panel-type"),
            "value": self.db.get_state("panel-value")}
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
                        if tag in self.__panel_tags:
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

        if self.__selected_mode["type"] == "panel":
            sorts = self._sorts + self.__class__.default_sorts
            medias = self.library.search(self.__filter, sorts)
            self._media_list.set(medias)
            self.__update_current()
            self.dispatch_signame(self.__class__.source_signal)

    def __update_active_list(self, type, pl_id, raise_ex = False):
        need_sort, sorts = False, self._sorts + self.__class__.default_sorts
        if type == "playlist":
            try: medias = self._get_playlist_content(pl_id)
            except SourceError: # playlist does not exist, set to panel
                if raise_ex:
                    raise SourceError(_("Playlist with id %s not found")\
                            % str(pl_id))
                self.__selected_mode["type"] = "panel";
                medias = self.library.search(self.__filter, sorts)
            else:
                need_sort = True
        elif type == "panel":
            medias = self.library.search(self.__filter, sorts)
        else:
            raise TypeError
        self._media_list.set(medias)
        if need_sort: self._media_list.sort(self._sorts)

    def __update_current(self):
        if self._current and self._current["id"] != -1: # update current id
            media_id = self._current["media_id"]
            try:
                self._current["id"] = self._media_list.find_id(media_id)
            except ValueError:
                self._current["id"] = -1

    def get_panel_tags(self):
        return self.__panel_tags

    def set_panel_filters(self, tag, values):
        if tag not in self.__panel_tags:
            raise SourceError(_("Tag '%s' not supported") % tag)
        if not values:
            self.remove_panel_filters(tag)
            return
        filter = Or()
        for value in values:
            filter.combine(Equals(tag, value))
        if tag in self.__panel and self.__panel[tag].equals(filter):
            return # do not need update
        self.__panel[tag] = filter

        # remove filter for panels at the right of this tag
        for tg in reversed(self.get_panel_tags()):
            if tg == tag: break
            try: del self.__panel[tg]
            except KeyError:
                pass

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
            raise SourceError(_("Tag '%s' not supported") % tag)
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

    def get_active_list(self):
        return self.__selected_mode

    def set_active_list(self, type, pl_id):
        if type == self.__selected_mode["type"]\
                and pl_id == self.__selected_mode["value"]:
            return # we do not need to update panel
        self.__update_active_list(type, pl_id, raise_ex = True)
        self.__selected_mode = {"type": type, "value": pl_id}
        self.__update_current()
        self.dispatch_signame(self.__class__.source_signal)

    def get_content(self, start = 0, stop = None):
        if self.__selected_mode["type"] == "panel":
            return self._media_list.get(start, stop), self.__filter,\
                    self._sorts
        elif self.__selected_mode["type"] == "playlist":
            return self._media_list.get(start, stop), None, self._sorts

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
        ml_id = self.db.set_magic_medialist_filters(self.base_medialist,\
                filter_list)
        # save panel sorts
        self.db.set_magic_medialist_sorts(ml_id, self._sorts)

    #
    # callback for deejayd signal
    #
    def cb_playlist_update(self, signal):
        pl_id = int(signal.get_attr('pl_id'))
        if self.__selected_mode["type"] == "playlist"\
                and pl_id == int(self.__selected_mode["value"]):
            self.__update_active_list("playlist", pl_id, raise_ex = True)
            self.dispatch_signame(self.__class__.source_signal)

    def cb_playlist_listupdate(self, signal):
        if self.__selected_mode["type"] == "playlist":
            pl_id = int(self.__selected_mode["value"])
            list = [int(id) \
                    for (id, pl, type) in self.db.get_medialist_list() if not \
                    pl.startswith("__") or not pl.endswith("__")]
            if pl_id not in list: # fall back to panel
                self.__update_active_list("panel", "", raise_ex = True)
                self.__selected_mode = {"type": "panel", "value": ""}
                self.dispatch_signame(self.__class__.source_signal)

# vim: ts=4 sw=4 expandtab
