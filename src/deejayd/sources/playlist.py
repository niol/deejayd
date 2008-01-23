# Deejayd, a media player daemon
# Copyright (C) 2007 Mickael Royer <mickael.royer@gmail.com>
#                    Alexandre Rossi <alexandre.rossi@gmail.com>
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

import os, random
from deejayd.sources._base import _BaseSource, MediaList, MediaNotFoundError
from deejayd.mediadb.library import NotFoundException

def playlist_action(func):
    def playlist_action_func(self, *__args, **__kw):
        if __kw.has_key('playlist') and __kw['playlist']:
            pls_name = __kw['playlist']
            del __kw['playlist']
            pls_obj = MediaList(self.db)
            pls_obj.load_playlist(pls_name, self.library.get_root_path())
        else:
            pls_obj = None

        __kw['playlist'] = pls_obj
        rs = func(self, *__args, **__kw)
        if pls_obj != None:
            self.db.delete_medialist(pls_name)
            self.db.save_medialist(pls_obj.get(), pls_name)
        return rs

    return playlist_action_func

class PlaylistSource(_BaseSource):
    pls_name = "__djcurrent__"
    name = "playlist"

    def __init__(self,db,library):
        _BaseSource.__init__(self,db)

        # Load current playlist
        self.library = library
        self._media_list = MediaList(self.db, self.get_recorded_id())
        self._media_list.load_playlist(self.pls_name, library.get_root_path())

    def get_list(self):
        list = [pl for (pl,) in self.db.get_medialist_list() if not \
            pl.startswith("__") or not pl.endswith("__")]
        return list

    def load_playlist(self, playlists, pos = None):
        for pls in playlists:
            self._media_list.load_playlist(pls,\
                self.library.get_root_path(), pos)
        self.dispatch_signame('player.current')

    @playlist_action
    def get_content(self,playlist = None):
        media_list = playlist or self._media_list
        return media_list.get()

    @playlist_action
    def add_path(self,paths,playlist = None,pos = None):
        media_list = playlist or self._media_list

        songs = []
        if isinstance(paths,str):
            paths = [paths]
        for path in paths:
            try: songs.extend(self.library.get_all_files(path))
            except NotFoundException:
                # perhaps it is file
                try: songs.extend(self.library.get_file(path))
                except NotFoundException: raise MediaNotFoundError

        media_list.add_media(songs,pos)
        if playlist:
            self.dispatch_signame('playlist.update')
        else:
            self.dispatch_signame('player.plupdate')

    @playlist_action
    def shuffle(self, playlist = None):
        media_list = playlist or self._media_list
        media_list.shuffle()
        if playlist:
            self.dispatch_signame('playlist.update')
        else:
            self.dispatch_signame('player.plupdate')

    @playlist_action
    def move(self, id, new_pos, type = "id", playlist = None):
        media_list = playlist or self._media_list
        media_list.move(id, new_pos, type)
        if playlist:
            self.dispatch_signame('playlist.update')
        else:
            self.dispatch_signame('player.plupdate')

    @playlist_action
    def clear(self, playlist = None):
        media_list = playlist or self._media_list
        if playlist == None:
            self._current = None
        media_list.clear()
        if playlist:
            self.dispatch_signame('playlist.update')
        else:
            self.dispatch_signame('player.plupdate')

    @playlist_action
    def delete(self, id, type = "id", playlist = None):
        media_list = playlist or self._media_list
        media_list.delete(id, type)
        if playlist:
            self.dispatch_signame('playlist.update')
        else:
            self.dispatch_signame('player.plupdate')

    def save(self, playlist_name):
        self.db.delete_medialist(playlist_name)
        self.db.save_medialist(self._media_list.get(), playlist_name)
        if playlist_name == self.pls_name:
            self.dispatch_signame('player.plupdate')
        else:
            self.dispatch_signame('playlist.update')

    def rm(self, playlist_name):
        self.db.delete_medialist(playlist_name)
        self.dispatch_signame('playlist.update')

    def close(self):
        _BaseSource.close(self)
        self.save(self.pls_name)

# vim: ts=4 sw=4 expandtab
