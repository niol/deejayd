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

import os
import urllib

from twisted.internet import reactor
from deejayd.component import SignalingComponent
from deejayd.mediadb.library import NotFoundException
from deejayd.sources._medialist import SimpleMediaList, MediaList
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
        self._media_list = MediaList(self.get_recorded_id() + 1)
        self.library = library
        self.library.connect_to_changes(self.cb_library_changes)

        if self.has_repeat:
            self._media_list.repeat = int(db.get_state(self.name+"-repeat"))
        self._playorder = orders[db.get_state(self.name+"-playorder")]


    def set_option(self, name, value):
        if name == "playorder":
            try: self._playorder = orders[value]
            except KeyError:
                raise SourceError(_("Unable to set %s order, not supported") %
                    value)
        elif name == "repeat" and self.has_repeat:
            self._media_list.repeat = int(value)
        else: raise NotImplementedError

    def cb_library_changes(self, action, file_id, threaded = True):
        if action == "remove":
            reactor.callFromThread(self._remove_media, file_id)
        elif action == "add": pass # not used for now
        elif action == "update":
            if threaded: reactor.callFromThread(self._update_media, file_id)
            else: self._update_media(file_id)

    def _update_media(self, media_id):
        media = self.library.get_file_withids([media_id])
        if self._media_list.update_media(media[0]):
            self.dispatch_signame(self.source_signal)

    def _remove_media(self, media_id):
        if self._media_list.remove_media(media_id):
            self.dispatch_signame(self.source_signal)

    def _get_playlist_content(self, pls):
        rs = self.db.get_static_medialist(pls, infos=self.library.media_attr)
        if len(rs) == 0 and (not pls.startswith("__") or \
                             not pls.endswith("__")):
            raise SourceError(_("Playlist %s does not exist.") % pls)
        return rs

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


class _BaseAudioLibSource(_BaseLibrarySource):
    base_medialist = ''

    def __init__(self, db, audio_library):
        super(_BaseAudioLibSource, self).__init__(db, audio_library)
        self.load_playlist((self.base_medialist,))

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

    def load_playlist(self, playlists, pos = None):
        medias = []
        for pls in playlists:
            medias.extend(self._get_playlist_content(pls))
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
