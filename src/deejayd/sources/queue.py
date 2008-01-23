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

from deejayd.mediadb.library import NotFoundException
from deejayd.sources._base import _BaseSource, MediaList, MediaNotFoundError

class QueueSource(_BaseSource):
    name = "queue"

    def __init__(self, db, audio_library, video_library):
        _BaseSource.__init__(self,db)
        self._media_list = MediaList(db, self.get_recorded_id())
        self.audio_lib = audio_library
        self.video_lib = video_library

    def add_path(self, paths, type = "audio", pos = None):
        library = type == "audio" and self.audio_lib or self.video_lib
        medias = []
        for path in paths:
            try: medias.extend(library.get_all_files(path))
            except NotFoundException:
                try: medias.extend(library.get_file(path))
                except NotFoundException: raise MediaNotFoundError

        self._media_list.add_media(medias, pos)
        self.dispatch_signame('queue.update')

    def delete(self, id):
        _BaseSource.delete(self, id)
        self.dispatch_signame('queue.update')

    def load_playlist(self, playlists, pos = None):
        for pls in playlists:
            self._media_list.load_playlist(pls,\
                self.audio_lib.get_root_path(), pos)

    def go_to(self,nb,type = "id"):
        _BaseSource.go_to(self,nb,type)
        if self._current != None:
            self._media_list.delete(nb, type)
        return self._current

    def next(self,rd,rpt):
        self.go_to(0,'pos')
        return self._current

    def previous(self,rd,rpt):
        # Have to be never called
        raise NotImplementedError

    def reset(self):
        self._current = None

# vim: ts=4 sw=4 expandtab
