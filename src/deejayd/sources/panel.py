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

from deejayd.sources._base import *

class Panel(UnknownSource):

    def filter(self):

class PanelSource(UnknownSourceManagement):
    name = "panel"

    def __init__(self, db, audio_library):
        UnknownSourceManagement.__init__(self,db)

        # Init parms
        self.current_source = Panel(self.db, self.get_recorded_id())
        self.__artist_list = None
        self.__album_list = None
        self.__genre_list = None
        self.__current = {"genre": None, "artist": None, "album": None}

    def set(self, tags = {}):
        self.__artist_list = self.audio_library.get_artist_list(tags)
        self.__current = tags
        self.album = self.db.get_artist_list(tags)

    def filters(self, type, content):

    def get(self):
        return {
            "genre": self.__current["genre"],
            "artist": self.__current["artist"],
            "album": self.__current["album"],
            "genre_list": self.__genre_list,
            "songs": self.current_source.get_contents()
            }

    def close(self):
        UnknownSourceManagement.close(self)

# vim: ts=4 sw=4 expandtab
