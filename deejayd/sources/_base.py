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

    def __init__(self, db):
        super(_BaseSource, self).__init__()
        self.state_name = "%s_state" % self.name
        self.load_state()

        self.db = db
        self._current = None
        self._playorder = orders["inorder"]

    def get_recorded_id(self):
        return self.state["id"]

    def get(self, start=0, length=None):
        def to_json(pl_entry, pos):
            m = pl_entry.get_media()
            if not isinstance(m, dict):
                m = m.to_json()
            m["id"] = pl_entry.get_id()
            m["pos"] = pos
            return m

        medias, filter, sort = self.get_content(start, length)
        rs = {
            "medias": map(to_json, medias, range(1, len(medias))),
            "filter": filter,
            "sort": sort
        }
        return rs

    def get_content(self, start=0, length=None):
        # medias, filter (None if useless), sort (None if useless)
        return self._media_list.get(start, length), None, None

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
            (self.name, self._media_list.get_id()),
            (self.name + "length", len(self._media_list)),
            (self.name + "timelength", self._media_list.time_length)
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
    medialist_type = "static"
    base_medialist = ''

    def __init__(self, db, library):
        super(_BaseLibrarySource, self).__init__(db)
        if self.medialist_type == "static":
            self._media_list = PlaylistFactory().static(library,
                                                        self.base_medialist)
        else:
            self._media_list = PlaylistFactory().magic(library,
                                                       self.base_medialist)
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
            raise NotImplementedError

    def get_status(self):
        status = super(_BaseLibrarySource, self).get_status()
        status.append((self.name + "playorder", self._playorder.name))
        if self.has_repeat:
            status.append((self.name + "repeat", self._media_list.repeat))
        return status

    def close(self):
        super(_BaseLibrarySource, self).close()
        self._media_list.save()

    def cb_library_changes(self, signal):
        file_id = signal.get_attr("id")
        getattr(self, "_%s_media" % signal.get_attr("type"))(file_id)

    def _add_media(self, media_id):
        pass

    def _update_media(self, media_id):
        try: media = self.library.get_file_withids([media_id])
        except NotFoundException:
            return
        if self._media_list.update_media(media[0]):
            self.dispatch_signame(self.source_signal)

    def _remove_media(self, media_id):
        if self._media_list.remove_media(media_id):
            self.dispatch_signame(self.source_signal)


class _BaseSortedLibSource(_BaseLibrarySource):
    medialist_type = "magic"

    def set_sort(self, sorts):
        for (tag, direction) in sorts:
            if tag not in self.sort_tags:
                raise SourceError(_("Tag '%s' not supported for sort") % tag)
            if direction not in ('ascending', 'descending'):
                raise SourceError(_("Bad sort direction for source"))
        self._sorts = sorts
        self._media_list.sort(self._sorts)
        self.dispatch_signame(self.source_signal)


class _BaseAudioLibSource(_BaseLibrarySource):
    base_medialist = ''
    medialist_type = "static"

    def add_song(self, song_ids, pos=None):
        try: medias = self.library.get_file_withids(song_ids)
        except NotFoundException:
            raise SourceError(_("One of these ids %s not found") % \
                ",".join(map(str, song_ids)))
        self._media_list.add(medias, pos)
        self.dispatch_signame(self.source_signal)

    def add_path(self, paths, pos=None):
        medias = []
        for path in paths:
            try: medias.extend(self.library.get_all_files(path))
            except NotFoundException:
                try: medias.extend(self.library.get_file(path))
                except NotFoundException:
                    raise SourceError(_("%s not found") % path)
        self._media_list.add(medias, pos)
        self.dispatch_signame(self.source_signal)

    def load_playlist(self, pl_ids, pos=None):
        try:
            pls_list = [PlaylistFactory().load_byid(self.library, pl_id)
                        for pl_id in pl_ids]
        except IndexError:
            raise DeejaydError(_("Some asked playlist are not found."))
        self._media_list.add(reduce(lambda ms, p: ms + p.get(), pls_list, []))
        self.dispatch_signame(self.source_signal)

    def move(self, ids, new_pos):
        if not self._media_list.move(ids, new_pos):
            raise SourceError(_("Unable to move selected medias"))
        self.dispatch_signame(self.source_signal)

    def remove(self, ids):
        super(_BaseAudioLibSource, self).remove(ids)
        self.dispatch_signame(self.source_signal)

    def clear(self):
        self._current = None
        self._media_list.clear()
        self.dispatch_signame(self.__class__.source_signal)

# vim: ts=4 sw=4 expandtab
