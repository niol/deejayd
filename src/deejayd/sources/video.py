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

from os import path
from deejayd.mediadb.library import NotFoundException
from deejayd.sources._base import ItemNotFoundException,UnknownSource,\
                            UnknownSourceManagement
class Video(UnknownSource):

    def save(self):pass


class VideoSource(UnknownSourceManagement):
    name = "video"

    def __init__(self, db, library):
        UnknownSourceManagement.__init__(self,db,library)

        # Init parms
        self.current_source = Video(db,library)
        self.__current_dir = ""
        try: self.set_directory(self.db.get_state("videodir"))
        except NotFoundException: pass

    def set_directory(self,dir):
        try: video_list = self.library.get_dir_files(dir)
        except NotFoundException:
            dirs = self.library.get_dir_content(dir)
            video_list = []

        self.current_source.clear()
        self.current_source.add_files(video_list)
        self.__current_dir = dir

    def get_current_dir(self):
        return self.__current_dir

    def get_status(self):
        return [('video_dir',self.__current_dir)]

    def close(self):
        self.db.set_state([(self.__current_dir,"videodir")])

# vim: ts=4 sw=4 expandtab
