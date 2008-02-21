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
from deejayd.mediadb.library import NotFoundException
from deejayd.sources._base import _BaseSource, SimpleMediaList, \
                                  MediaNotFoundError

class VideoSource(_BaseSource):
    name = "video"
    list_name = "__videocurrent__"

    def __init__(self, db, library):
        _BaseSource.__init__(self, db)
        self.library = library
        self._media_list = SimpleMediaList(self.get_recorded_id())

        # load saved
        content = self.db.get_videolist(self.list_name)
        medias = []
        for (pos, dir, fn, title, len, w, h, sub, id) in content:
            medias.append({
                "filename": fn, "dir": dir, "length": len, "videowidth": w,
                "videoheight": h, "external_subtitle": sub,
                "type": "video", "title": title, "media_id":id,
                "uri": "file://" + os.path.join(self.library.get_root_path(), \
                                                dir, fn),
                })
        self._media_list.set(medias)

    def set(self, type, value):
        if type == "directory":
            try: video_list = self.library.get_all_files(value)
            except NotFoundException:
                raise MediaNotFoundError
        elif type == "search":
            video_list = self.library.search(value)
        else:
            raise ValueError

        self._media_list.set(video_list)

    def close(self):
        _BaseSource.close(self)
        # record video list in the db
        self.db.delete_medialist(self.list_name)
        self.db.save_medialist(self._media_list.get(), self.list_name)

# vim: ts=4 sw=4 expandtab
