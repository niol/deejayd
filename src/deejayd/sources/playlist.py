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

import os, random
from deejayd.sources._base import _BaseAudioLibSource, SourceError
from deejayd.mediadb.library import NotFoundException

def playlist_action(func):
    def playlist_action_func(self, *__args, **__kw):
        if __kw.has_key('playlist') and __kw['playlist']:
            pls_name = __kw['playlist']
            del __kw['playlist']
            pls_obj = MediaList()
            content = self.db.get_static_medialist(pls_name,\
                                    self.library.media_attr)
            if not len(content):
                raise SourceError(_("Playlist %s Not found") % pls_name)
            pls_obj.add_media(self.library._format_db_answer(content))
        else:
            pls_obj = None

        __kw['playlist'] = pls_obj
        rs = func(self, *__args, **__kw)
        if pls_obj != None:
            self.db.set_static_medialist(pls_name, pls_obj)
        return rs

    return playlist_action_func

class PlaylistSource(_BaseAudioLibSource):
    base_medialist = "__djcurrent__"
    name = "playlist"
    source_signal = 'player.plupdate'

    def get_list(self):
        list = [pl for (pl,) in self.db.get_medialist_list() if not \
            pl.startswith("__") or not pl.endswith("__")]
        return list

    @playlist_action
    def get_content(self,start = 0, stop = None, playlist = None):
        media_list = playlist or self._media_list
        return media_list.get(start, stop)

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
                except NotFoundException:
                    raise SourceError(_("path %s not found") % path)
        media_list.add_media(songs,pos)

        if playlist:
            self.dispatch_signame('playlist.update')
        else:
            if pos: self._media_list.reload_item_pos(self._current)
            self.dispatch_signame('player.plupdate')

    @playlist_action
    def shuffle(self, playlist = None):
        media_list = playlist or self._media_list
        media_list.shuffle(self._current)
        if self._current: self._current["pos"] = 0
        if playlist:
            self.dispatch_signame('playlist.update')
        else:
            self._media_list.reload_item_pos(self._current)
            self.dispatch_signame('player.plupdate')

    @playlist_action
    def move(self, ids, new_pos, playlist = None):
        media_list = playlist or self._media_list
        type = playlist and "pos" or "id"
        if not media_list.move(ids, new_pos, type):
            raise SourceError(_("Unable to move selected ids"))
        if playlist:
            self.dispatch_signame('playlist.update')
        else:
            self._media_list.reload_item_pos(self._current)
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
    def delete(self, ids, playlist = None):
        media_list = playlist or self._media_list
        type = playlist and "pos" or "id"
        if not media_list.delete(ids, type):
            raise SourceError(_("Unable to delete selected ids"))
        if playlist:
            self.dispatch_signame('playlist.update')
        else:
            self._media_list.reload_item_pos(self._current)
            self.dispatch_signame('player.plupdate')

    def save(self, playlist_name):
        self.db.set_static_medialist(playlist_name, self._media_list.get())
        self.dispatch_signame('playlist.update')

    def rm(self, playlist_name):
        self.db.delete_static_medialist(playlist_name)
        self.dispatch_signame('playlist.update')

# vim: ts=4 sw=4 expandtab
