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

import os, locale

from twisted.internet import reactor
from deejayd import mediafilters
from deejayd.component import SignalingComponent
from deejayd.mediadb.library import NotFoundException
from deejayd.sources._medialist import *
from deejayd.sources._playorder import orders

class SourceError(Exception):
    # Handle unicode messages, what Exceptions cannot. See Python issue at
    # http://bugs.python.org/issue2517
    def __str__(self):
        if type(self.message) is unicode:
            return str(self.message.encode(locale.getpreferredencoding()))
        else:
            return str(self.message)


class _BaseSource(SignalingComponent):
    name = "unknown"

    def __init__(self, db):
        super(_BaseSource, self).__init__()
        self.db = db
        self._current = None
        self._playorder = orders["inorder"]

    def get_recorded_id(self):
        id = int(self.db.get_state(self.name+"id"))
        return id

    def get_content(self, start = 0, stop = None):
        return self._media_list.get(start, stop)

    def get_current(self):
        return self._current

    def go_to(self, id, type = "id"):
        if type == "pos":
            try: id = self._media_list._order[id]
            except IndexError: return None
        self._current = self._playorder.set_explicit(self._media_list, id)
        return self._current

    def delete(self, ids):
        if not self._media_list.delete(ids):
            raise SourceError(_("Unable to delete selected ids"))
        self._media_list.reload_item_pos(self._current)

    def clear(self):
        self._media_list.clear()
        self._playorder.reset(self._media_list)

    def next(self, explicit = True):
        if explicit:
            self._current = self._playorder.next_explicit(self._media_list,\
                                                          self._current)
        else:
            self._current = self._playorder.next_implicit(self._media_list,\
                                                          self._current)
        return self._current

    def previous(self):
        self._current = self._playorder.previous_explicit(self._media_list,\
                                                          self._current)
        return self._current

    def get_status(self):
        return [
            (self.name, self._media_list.list_id),
            (self.name+"length", len(self._media_list)),
            (self.name+"timelength", self._media_list.time_length)
            ]

    def set_option(self, name, value):
        raise NotImplementedError

    def close(self):
        states = [ (str(self._media_list.list_id),self.__class__.name+"id") ]
        self.db.set_state(states)


class _BaseLibrarySource(_BaseSource):
    available_playorder = ("inorder", "random", "onemedia","random-weighted")
    has_repeat = True
    source_signal = ''

    def __init__(self, db, library):
        super(_BaseLibrarySource, self).__init__(db)
        if self.medialist_type == "sorted":
            self._media_list = SortedMediaList(self.get_recorded_id() + 1)
        elif self.medialist_type == "unsorted":
            self._media_list = UnsortedMediaList(self.get_recorded_id() + 1)
        self.library = library

        if self.has_repeat:
            self._media_list.repeat = int(db.get_state(self.name+"-repeat"))
        self._playorder = orders[db.get_state(self.name+"-playorder")]

    def _get_playlist_content(self, pl_id):
        try:
            pl_id, name, type = self.db.is_medialist_exists(pl_id)
            if type == "static":
                return self.db.get_static_medialist(pl_id,\
                    infos=self.library.media_attr)
            elif type == "magic":
                properties = dict(self.db.get_magic_medialist_properties(pl_id))
                if properties["use-or-filter"] == "1":
                    filter = mediafilters.Or()
                else:
                    filter = mediafilters.And()
                sorts = [("album", "ascending"), ("tracknumber", "ascending")]
                if properties["use-limit"] == "1":
                    sorts = [(properties["limit-sort-value"],\
                             properties["limit-sort-direction"])] + sorts
                    limit = int(properties["limit-value"])
                else:
                    limit = None
                filter.filterlist = self.db.get_magic_medialist_filters(pl_id)
                return self.library.search(filter, sorts, limit)
        except TypeError:
            raise SourceError(_("Playlist %s does not exist.") % str(pl_id))

    def set_option(self, name, value):
        if name == "playorder":
            try: self._playorder = orders[value]
            except KeyError:
                raise SourceError(_("Unable to set %s order, not supported") %
                    value)
        elif name == "repeat" and self.has_repeat:
            self._media_list.repeat = int(value)
        else: raise NotImplementedError

    def get_status(self):
        status = super(_BaseLibrarySource, self).get_status()
        status.append((self.name+"playorder", self._playorder.name))
        if self.has_repeat:
            status.append((self.name+"repeat", self._media_list.repeat))
        return status

    def close(self):
        super(_BaseLibrarySource, self).close()
        self.db.set_static_medialist(self.base_medialist,self._media_list.get())
        states = [(self._playorder.name, self.name+"-playorder")]
        if self.has_repeat:
            states.append((self._media_list.repeat, self.name+"-repeat"))
        self.db.set_state(states)

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
    medialist_type = "sorted"

    def set_sorts(self, sorts):
        for (tag, direction) in sorts:
            if tag not in self.sort_tags:
                raise SourceError(_("Tag '%s' not supported for sort") % tag)
            if direction not in ('ascending', 'descending'):
                raise SourceError(_("Bad sort direction for panel") % tag)
        self._sorts = sorts
        self._media_list.sort(self._sorts + self.default_sorts)
        self.dispatch_signame(self.source_signal)


class _BaseAudioLibSource(_BaseLibrarySource):
    base_medialist = ''
    medialist_type = "unsorted"

    def __init__(self, db, audio_library):
        super(_BaseAudioLibSource, self).__init__(db, audio_library)
        # load saved
        try: ml_id = self.db.get_medialist_id(self.base_medialist, 'static')
        except ValueError: # medialist does not exist
            pass
        else:
            self._media_list.set(self._get_playlist_content(ml_id))

    def add_song(self, song_ids, pos = None):
        try: medias = self.library.get_file_withids(song_ids)
        except NotFoundException:
            raise SourceError(_("One of these ids %s not found") % \
                ",".join(map(str, song_ids)))
        self._media_list.add_media(medias, pos)
        if pos: self._media_list.reload_item_pos(self._current)
        self.dispatch_signame(self.source_signal)

    def add_path(self, paths, pos = None):
        medias = []
        for path in paths:
            try: medias.extend(self.library.get_all_files(path))
            except NotFoundException:
                try: medias.extend(self.library.get_file(path))
                except NotFoundException:
                    raise SourceError(_("%s not found") % path)
        self._media_list.add_media(medias, pos)
        if pos: self._media_list.reload_item_pos(self._current)
        self.dispatch_signame(self.source_signal)

    def load_playlist(self, pl_ids, pos = None):
        medias = []
        for id in pl_ids:
            medias.extend(self._get_playlist_content(id))
        self._media_list.add_media(medias, pos)
        if pos: self._media_list.reload_item_pos(self._current)
        self.dispatch_signame(self.source_signal)

    def move(self, ids, new_pos):
        if not self._media_list.move(ids, new_pos):
            raise SourceError(_("Unable to move selected medias"))
        self._media_list.reload_item_pos(self._current)
        self.dispatch_signame(self.source_signal)

    def delete(self, ids):
        super(_BaseAudioLibSource, self).delete(ids)
        self.dispatch_signame(self.source_signal)

    def clear(self):
        self._current = None
        self._media_list.clear()
        self.dispatch_signame(self.__class__.source_signal)

# vim: ts=4 sw=4 expandtab
