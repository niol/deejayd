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

from deejayd import DeejaydError
from deejayd.component import SignalingComponent, JSONRpcComponent
from deejayd.component import PersistentStateComponent
from deejayd.mediadb.library import NotFoundException
from deejayd.model.playlist import PlaylistFactory
from deejayd.sources._playorder import orders


class SourceError(DeejaydError): pass


class _BaseSource(SignalingComponent, JSONRpcComponent, \
                  PersistentStateComponent):
    name = "unknown"
    initial_state = {"id": 1}

    def __init__(self):
        super(_BaseSource, self).__init__()
        self.state_name = "%s_state" % self.name
        self.load_state()

        self._current = None
        self._playorder = orders["inorder"]

    def get_recorded_id(self):
        return self.state["id"]

    def get(self, start=0, length=None):
        return self._media_list.get(start, length)

    def get_current(self):
        return self._current

    def go_to(self, id, type="id"):
        if type == "pos":
            try: id = self._media_list._playlist[id]["id"]
            except IndexError: return None
        self._current = self._playorder.set_explicit(self._media_list, id)
        return self._current

    def remove(self, ids):
        if not self._media_list.delete(ids):
            raise SourceError(_("Unable to delete selected ids"))

    def clear(self):
        self._media_list.clear()
        self._playorder.reset(self._media_list)

    def next(self, explicit=True):
        if explicit:
            self._current = self._playorder.next_explicit(self._media_list, \
                                                          self._current)
        else:
            self._current = self._playorder.next_implicit(self._media_list, \
                                                          self._current)
        return self._current

    def previous(self):
        self._current = self._playorder.previous_explicit(self._media_list, \
                                                          self._current)
        return self._current

    def get_status(self):
        return [
            ("id", self._media_list.get_id()),
            ("length", len(self._media_list)),
            ("timelength", self._media_list.time_length)
            ]

    def set_option(self, name, value):
        raise NotImplementedError

    def close(self):
        self.state["id"] = self._media_list.get_id()
        super(_BaseSource, self).close()


class _BaseLibrarySource(_BaseSource):
    available_playorder = ("inorder", "random", "onemedia", "random-weighted")
    has_repeat = True
    initial_state = {"id": 1, "playorder": "inorder", "repeat": False}
    source_signal = ''
    mlist_name = ''

    def __init__(self, library):
        super(_BaseLibrarySource, self).__init__()
        self._media_list = PlaylistFactory().static(library, self.mlist_name)
        self._media_list.set_id(self.get_recorded_id() + 1)
        self._media_list.set_source(self.name)
        self.library = library

        if self.has_repeat:
            self._media_list.repeat = self.state["repeat"]
        self._playorder = orders[self.state["playorder"]]

    def set_option(self, name, value):
        if name == "playorder":
            try: self._playorder = orders[value]
            except KeyError:
                raise SourceError(_("Unable to set %s order, not supported") %
                    value)
            else:
                self.state["playorder"] = value
        elif name == "repeat" and self.has_repeat:
            if not isinstance(value, bool):
                raise SourceError(_("Option value has to be a boolean"))
            self._media_list.repeat = value
            self.state["repeat"] = value
        else:
            raise DeejaydError(_("Option %s not supported"))
        self.dispatch_signame(self.source_signal)

    def _load_medias(self, medias, queue):
        if queue:
            self._media_list.add(medias)
        else:
            self._media_list.set(medias)
        self.dispatch_signame(self.source_signal)

    def add_media_by_ids(self, media_ids, queue=True):
        medias = self.library.get_file_withids(media_ids)
        if len(medias) < len(media_ids):
            raise SourceError(_("One of these media ids %s not found") % \
                              ",".join(map(str, media_ids)))
        self._load_medias(medias, queue)

    def load_folders(self, f_ids, queue=True):
        self._load_medias(self.library.get_all_files(f_ids), queue)

    def add_media_by_filter(self, ft, queue=True):
        medias = self.library.search(ft)
        self._load_medias(medias, queue)

    def remove(self, ids):
        super(_BaseLibrarySource, self).remove(ids)
        self.dispatch_signame(self.__class__.source_signal)

    def clear(self):
        super(_BaseLibrarySource, self).clear()
        self.dispatch_signame(self.__class__.source_signal)

    def shuffle(self):
        self._media_list.shuffle(self._current)
        self.dispatch_signame(self.__class__.source_signal)

    def get_status(self):
        status = super(_BaseLibrarySource, self).get_status()
        status.append(("playorder", self._playorder.name))
        if self.has_repeat:
            status.append(("repeat", self._media_list.repeat))
        return dict(status)

    def move(self, ids, new_pos):
        if not self._media_list.move(ids, new_pos):
            raise SourceError(_("Unable to move selected medias"))
        self.dispatch_signame(self.source_signal)

    def close(self):
        super(_BaseLibrarySource, self).close()
        self._media_list.save()

# vim: ts=4 sw=4 expandtab
