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

from deejayd.sources._base import _BaseAudioLibSource

class PlaylistSource(_BaseAudioLibSource):
    SUBSCRIPTIONS = {
            "mediadb.mupdate": "cb_library_changes",
            }
    base_medialist = "__djcurrent__"
    name = "playlist"
    source_signal = 'player.plupdate'

    def shuffle(self):
        self._media_list.shuffle(self._current)
        if self._current: self._current["pos"] = 0
        self.dispatch_signame(self.__class__.source_signal)

    def save(self, playlist_name):
        id = self.db.set_static_medialist(playlist_name, self._media_list.get())
        self.dispatch_signame('playlist.listupdate')
        return {"playlist_id": id}

# vim: ts=4 sw=4 expandtab
