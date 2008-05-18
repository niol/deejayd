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
import random, urllib

from twisted.internet import reactor
from deejayd.component import SignalingComponent
from deejayd.mediadb.library import NotFoundException


class MediaNotFoundError(Exception):pass
class PlaylistNotFoundError(Exception):pass


class SimpleMediaList:

    def __init__(self, id = 0):
        self._list_id = id
        self._media_id = 0
        self._time_length = 0
        self._content = []

    def _update_list_id(self):
        self._list_id += 1
        # update time length
        self._time_length = 0
        for m in self._content:
            try: length = int(m["length"])
            except (IndexError, ValueError, TypeError):
                continue
            if length:
                self._time_length += length

    def __len__(self):
        return len(self._content)

    def __getitem__(self, key):
        if isinstance(key, int):
            ans = {"pos": key}
            ans.update(self._content[key])
        else:
            ans = []
            for i, media in enumerate(self._content[key]):
                m = {"pos": i}
                m.update(media)
                ans.append(m)
        return ans

    def __iter__(self):
        return self._content.__iter__()

    def set(self, medias):
        self._content = []
        self.add_media(medias)

    def add_media(self, medias, first_pos = None):
        if first_pos == None:
            first_pos = len(self._content)

        for index, m in enumerate(medias):
            m["id"] = self.set_media_id()
            self._content.insert(first_pos + index, m)
        self._update_list_id()

    def clear(self):
        self._content = []
        self._update_list_id()

    def delete(self, id, type = "id"):
        indexes = []
        for index, media in enumerate(self._content):
            if media[type] == id:
                indexes.append(index)
        if len(indexes) == 0: raise MediaNotFoundError
        for i in indexes: del self._content[i]

        self._update_list_id()

    def get_ids(self):
        return [m["id"] for m in self._content]

    def get_from_id(self, id):
        media = None
        for idx, m in enumerate(self._content):
            if m["id"] == id:
                return self[idx]
        raise MediaNotFoundError

    def get_time_length(self):
        return self._time_length

    def get_list_id(self):
        return self._list_id

    def next(self, media_id):
        for index, media in enumerate(self._content):
            if media["id"] == media_id:
                return self[index+1]
        raise IndexError

    def previous(self, media_id):
        for index, media in enumerate(self._content):
            if media["id"] == media_id:
                return self[index-1]
        raise IndexError

    def set_media_id(self):
        self._media_id += 1
        return self._media_id


class MediaList(SimpleMediaList):

    def update_media(self, new_media):
        ans = False
        for idx, m in enumerate(self._content):
            if m["media_id"] == new_media["media_id"]:
                new_media["id"] = m["id"]
                self._content[idx] = new_media
                ans = True
        if ans: self._update_list_id()
        return ans

    def move(self, ids, new_pos, type):
        medias = [m for m in self._content if m["id"] in ids]

        old_content = self._content
        self._content = []
        for index, media in enumerate(old_content):
            if index == new_pos:
                self._content.extend(medias)
            if media not in medias:
                self._content.append(media)

        self._update_list_id()

    def shuffle(self, current = None):
        new_content = []
        old_content = self._content
        current_id = current and current["id"]

        while len(old_content) > 0:
            media = random.choice(old_content)
            if media["id"] == current_id:
                new_content.insert(0, media)
            else:
                new_content.append(media)
            del old_content[old_content.index(media)]

        self._content = new_content
        self._update_list_id()


class _BaseSource(SignalingComponent):
    name = "unknown"

    def __init__(self, db):
        SignalingComponent.__init__(self)
        self.db = db
        self._current = None
        self._played = []

    def get_recorded_id(self):
        id = int(self.db.get_state(self.name+"id"))
        return id

    def get_content(self):
        return self._media_list
        ans = []
        for idx, m in enumerate(self._media_list):
            ans.append(self._media_list[idx])
        return ans

    def get_current(self):
        return self._current

    def go_to(self, id, type = "id"):
        self._played = []
        if type == "pos":
            try: self._current = self._media_list[id]
            except IndexError:
                self._current = None
        else:
            try: self._current = self._media_list.get_from_id(id)
            except MediaNotFoundError:
                self._current = None

        if self._current and self._current["id"] not in self._played:
            self._played.append(self._current["id"])
        return self._current

    def _reload_current(self):
        try:
            new_pos = self._media_list.get_from_id(self._current["id"])["pos"]
            self._current["pos"] = new_pos
        except (TypeError, MediaNotFoundError):
            pass

    def delete(self, id):
        self._media_list.delete(id)
        try: self._played.remove(id)
        except ValueError:
            pass
        self._reload_current()

    def clear(self):
        self._media_list.clear()
        self._played = []

    def next(self, rd, rpt):
        if not self._media_list:
            self._current == None
            return self._current

        if self._current == None:
            if rd:
                id = random.choice(self._media_list.get_ids())
                self.go_to(id)
            else: self._current = self.go_to(0, "pos")
            return self._current

        # add current media in played list
        if self._current["id"] not in self._played:
            self._played.append(self._current["id"])

        # Return a pseudo-random song
        if rd:
            # first determine if the current song is in playedItems
            idx = self._played.index(self._current["id"])
            try: new_id = self._played[idx+1]
            except IndexError: pass
            else:
                self._current = self._media_list.get_from_id(new_id)
                return self._current

            # Determine the id of the next song
            values = [id for id in self._media_list.get_ids() \
                        if id not in self._played]
            try: new_id = random.choice(values)
            except IndexError: # All songs are played
                if rpt:
                    self._played = []
                    new_id = random.choice(self._content.get_ids())
                else:
                    self._current = None
                    return None

            # Obtain the choosed song
            try: self._current = self._media_list.get_from_id(new_id)
            except MediaNotFoundError:
                self._current = None
            return self._current

        try: self._current = self._media_list.next(self._current["id"])
        except IndexError:
            if rpt: self._current = self.go_to(0, "pos")
            else: self._current = None

        return self._current

    def previous(self,rd,rpt):
        if self._current == None:
            return None

        # add current media in played list
        if self._current["id"] not in self._played:
            self._played.append(self._current["id"])

        # Return the last pseudo-random media
        if rd:
            id = self._played.index(self._current["id"])
            if id == 0:
                self._current = None
                return self._current
            try:
                self._current = self._media_list.get_from_id(self._played[id-1])
            except MediaNotFoundError:
                self._current = None
            return self._current

        try: self._current = self._media_list.previous(self._current["id"])
        except IndexError:
            self._current = None

        return self._current

    def get_status(self):
        return [
            (self.name, self._media_list.get_list_id()),
            (self.name+"length", len(self._media_list)),
            (self.name+"timelength", self._media_list.get_time_length())
            ]

    def close(self):
        states = [
            (str(self._media_list.get_list_id()),self.__class__.name+"id")
            ]
        self.db.set_state(states)


class _BaseLibrarySource(_BaseSource):
    source_signal = ''

    def __init__(self, db, library):
        _BaseSource.__init__(self,db)
        self.library = library
        self.library.connect_to_changes(self.cb_library_changes)

    def cb_library_changes(self, action, file_id):
        if action == "remove":
            reactor.callFromThread(self._remove_media, file_id)
        elif action == "add":
            reactor.callFromThread(self._add_media, file_id)
        elif action == "update":
            reactor.callFromThread(self._update_media, file_id)
            pass

    def _add_media(self, media_id):
        pass

    def _update_media(self, media_id):
        media = self.library.get_file_withid(media_id)
        if self._media_list.update_media(media[0]):
            self.dispatch_signame(self.source_signal)

    def _remove_media(self, media_id):
        try: self._media_list.delete(media_id, "media_id")
        except MediaNotFoundError:
            return
        self.dispatch_signame(self.source_signal)


class _BaseAudioLibSource(_BaseLibrarySource):
    base_medialist = ''

    def __init__(self, db, audio_library):
        _BaseLibrarySource.__init__(self, db, audio_library)
        self._media_list = MediaList(self.get_recorded_id() + 1)
        self.load_playlist((self.base_medialist,))

    def add_path(self, paths, pos = None):
        medias = []
        for path in paths:
            try: medias.extend(self.library.get_all_files(path))
            except NotFoundException:
                try: medias.extend(self.library.get_file(path))
                except NotFoundException: raise MediaNotFoundError
        self._media_list.add_media(medias, pos)
        self._reload_current()

    def load_playlist(self, playlists, pos = None):
        medias = []
        for pls in playlists:
            content = self.db.get_static_medialist(pls,self.library.media_attr)
            if len(content) == 0 and (not pls.startswith("__") or \
                                      not pls.endswith("__")):
                raise PlaylistNotFoundError
            medias.extend(self.library._format_db_answer(content))
        self._media_list.add_media(medias, pos)
        self._reload_current()

    def close(self):
        _BaseLibrarySource.close(self)
        self.db.set_static_medialist(self.base_medialist,self._media_list)

# vim: ts=4 sw=4 expandtab
