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

from deejayd.jsonrpc.interfaces import PanelSourceModule, jsonrpc_module
from deejayd.model.mediafilters import *
from deejayd.model.playlist import PlaylistFactory
from deejayd.sources._base import _BaseSortedLibSource, SourceError
from deejayd.ui import log

@jsonrpc_module(PanelSourceModule)
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
            ['genre', 'artist', 'album'], \
            ['genre', 'various_artist', 'album'], \
            ['artist', 'album'], \
            ['various_artist', 'album'], \
            ]
    contains_tags = ('genre', 'artist', 'album', 'title', 'all')
    sort_tags = ('genre', 'artist', 'album', 'title', 'rating', 'tracknumber')
    initial_state = {"id": 1, "playorder": "inorder", "repeat": False, \
                     "panel-type": "panel", "panel-value": "0"}

    def __init__(self, library, config):
        super(PanelSource, self).__init__(library)
        self._media_list.load()
        self._panel_medialist = self._media_list

        # get panel tags
        self.__panel_tags = config.getlist("panel", "panel_tags")
        if self.__panel_tags not in self.supported_panel_tags:
            log.err(_("You choose wrong panel tags, fallback to default"))
            self.__panel_tags = ['genre', 'artist', 'album']
        p_filters = self._media_list.get_filters()
        self.__filters_to_parms(p_filters)

        # custom attributes
        self.__update_active_list(self.state["panel-type"], \
                                  self.state["panel-value"])

    def __filters_to_parms(self, filters=[]):
        # filter as AND(Search, Panel) with
        #  * Panel : And(OR(genre=value1, genre=value2), OR(artist=value1)...)
        #  * Search : OR(tag1 CONTAINS value, )
        self.__search, self.__panel = None, {}
        if filter != None:
            for ft in filters:
                if ft.get_name() == "and":  # panel
                    for panel_ft in ft.filterlist:
                        tag = panel_ft.filterlist[0].tag
                        if tag in self.__panel_tags:
                            self.__panel[tag] = panel_ft
                elif ft.get_name() == "or" or ft.type == "basic":  # search
                    self.__search = ft

    def __update_panel_filters(self):
        if self.state["panel-type"] == "panel":
            # rebuild filter
            filters = []
            if self.__search:
                filters.append(self.__search)
            filters.append(And(*self.__panel.values()))
            self._media_list.set_filters(filters)

            self.__update_current()
            self.dispatch_signame(self.__class__.source_signal)

    def __update_active_list(self, type, pl_id, raise_ex=False):
        current_id = self._media_list.get_id()
        if type == "playlist":
            try:
                self._media_list = PlaylistFactory().load_byid(self.library,
                                                                pl_id)
                if self._media_list.get_type() == "magic":
                    self._media_list.load()
                self._media_list.set_source("panel")
            except IndexError:  # playlist does not exist, set to panel
                if raise_ex:
                    raise SourceError(_("Playlist with id %s not found")\
                            % str(pl_id))
                self.state["panel-type"] = "panel";
                self._media_list = self._panel_medialist

        elif type == "panel":
            self._media_list = self._panel_medialist
        else:
            raise TypeError
        self._media_list.set_id(current_id + 1)

    def __update_current(self):
        if self._current and self._current["id"] != -1:  # update current id
            media_id = self._current["media_id"]
            try:
                self._current = self._media_list.find(media_id)
            except ValueError:
                self._current["id"] = -1

    def get_tags(self):
        return self.__panel_tags

    def set_filter(self, tag, values):
        if tag not in self.__panel_tags:
            raise SourceError(_("Tag '%s' not supported") % tag)
        if not values:
            self.remove_panel_filters(tag)
            return
        filter = Or()
        for value in values:
            filter.combine(Equals(tag, value))
        if tag in self.__panel and self.__panel[tag].equals(filter):
            return  # do not need update
        self.__panel[tag] = filter

        # remove filter for panels at the right of this tag
        for tg in reversed(self.get_tags()):
            if tg == tag: break
            try: del self.__panel[tg]
            except KeyError:
                pass

        self.__update_panel_filters()

    def remove_filter(self, tag):
        try: del self.__panel[tag]
        except KeyError:
            pass
        self.__update_panel_filters()

    def clear_filters(self):
        self.__panel = {}
        self.__update_panel_filters()

    def set_search_filter(self, tag, value):
        if tag not in self.__class__.contains_tags:
            raise SourceError(_("Tag '%s' not supported") % tag)
        if tag == "all":
            new_filter = Or()
            for tg in ('title', 'genre', 'artist', 'album'):
                new_filter.combine(Contains(tg, value))
        else:
            new_filter = Contains(tag, value)
        self.__search = new_filter
        self.__panel = {}  # remove old panel filter
        self.__update_panel_filters()

    def clear_search_filter(self):
        if self.__search:
            self.__search = None
            self.__update_panel_filters()

    def clear_all_filters(self):
        self.__search, self.__panel = None, {}
        self.__update_panel_filters()

    def get_active_list(self):
        return {"type": self.state["panel-type"], \
                 "value": self.state["panel-value"]}

    def set_active_list(self, type, pl_id=None):
        if type == self.state["panel-type"]\
                and pl_id == self.state["panel-value"]:
            return  # we do not need to update panel
        try:
            self.__update_active_list(type, pl_id, raise_ex=True)
        except TypeError:
            raise SourceError("Unknown panel source")
        self.state["panel-type"] = type
        self.state["panel-value"] = pl_id
        self.__update_current()
        self.dispatch_signame(self.__class__.source_signal)

    def get_content(self, start=0, length=None):
        stop = None
        if length is not None:
            stop = start + int(length)
        if self.state["panel-type"] == "panel":
            return self._media_list.get(start, stop), \
                    And(*self._media_list.get_filters()), \
                    self._media_list.get_sorts()
        elif self.state["panel-type"] == "playlist":
            return self._media_list.get(start, stop), None, None

    def set_sort(self, sorts):
        if self.state["panel-type"] == "panel":
            super(PanelSource, self).set_sort(sorts)

    def close(self):
        super(PanelSource, self).close()
        self._panel_medialist.save()

    #
    # callback for deejayd signal
    #
    def cb_playlist_update(self, signal):
        pl_id = int(signal.get_attr('pl_id'))
        if self.state["panel-type"] == "playlist"\
                and pl_id == int(self.state["panel-value"]):
            self.__update_active_list("playlist", pl_id, raise_ex=True)
            self.dispatch_signame(self.__class__.source_signal)

    def cb_playlist_listupdate(self, signal):
        if self.state["panel-type"] == "playlist":
            pl_id = int(self.state["panel-value"])
            list = [int(p["pl_id"]) for p in PlaylistFactory().list()]
            if pl_id not in list:  # fall back to panel
                self.__update_active_list("panel", "", raise_ex=True)
                self.state["panel-type"] = "panel"
                self.state["panel-value"] = ""
                self.dispatch_signame(self.__class__.source_signal)

# vim: ts=4 sw=4 expandtab
