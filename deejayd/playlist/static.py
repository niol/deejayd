# Deejayd, a media player daemon
# Copyright (C) 2007-2012 Mickael Royer <mickael.royer@gmail.com>
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

import deejayd.mediadb.library
from deejayd import DeejaydError
from deejayd.playlist import _Playlist

class StaticPlaylist(_Playlist):

    def content(self, first=0, length=-1):
        songs = self.db.get_static_medialist(self.pl_id,\
            infos = self.library.media_attr)
        last = length == -1 and len(songs) or int(first) + int(length)
        return songs[int(first):last], None, None

    def add(self, values, type="path"):
        ids = values
        if type == "path":
            ids = []
            for path in values:
                try: medias = self.library.get_all_files(path)
                except deejayd.mediadb.library.NotFoundException:
                    try: medias = self.library.get_file(path)
                    except deejayd.mediadb.library.NotFoundException:
                        raise DeejaydError(_('Path %s not found in library')\
                                % path)
                for m in medias: ids.append(m["media_id"])

        self.db.add_to_static_medialist(self.pl_id, ids)
        self.db.connection.commit()

    def remove(self, values):
        songs = self.db.get_static_medialist(self.pl_id, infos = [])
        ids = []
        for pos, song in enumerate(songs):
            if pos+1 not in values:
                ids.append(song["media_id"])
               
        self.db.clear_static_medialist(self.pl_id)
        self.db.add_to_static_medialist(self.pl_id, ids)
        self.db.connection.commit()

    def clear(self):
        self.db.clear_static_medialist(self.pl_id)

# vim: ts=4 sw=4 expandtab
