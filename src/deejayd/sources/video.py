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
from deejayd.sources._base import _BaseLibrarySource, SourceError

class VideoSource(_BaseLibrarySource):
    name = "video"
    base_medialist = "__videocurrent__"
    source_signal = 'video.update'

    def __init__(self, db, library):
        super(VideoSource, self).__init__(db, library)
        # load saved
        ans = self.db.get_static_medialist(self.base_medialist,\
            library.media_attr)
        self._media_list.set(library._format_db_answer(ans))

    def set(self, type, value):
        if type == "directory":
            try: video_list = self.library.get_all_files(value)
            except NotFoundException:
                raise SourceError(_("Directory %s not found") % value)
        elif type == "search":
            video_list = self.library.search(value)
        else:
            raise SourceError(_("type %s not supported") % type)

        self._media_list.set(video_list)
        self.dispatch_signame(self.source_signal)

# vim: ts=4 sw=4 expandtab
