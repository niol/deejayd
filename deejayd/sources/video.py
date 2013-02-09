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

from deejayd.jsonrpc.interfaces import VideoSourceModule, jsonrpc_module
from deejayd.mediadb.library import NotFoundException
from deejayd.sources._base import _BaseSortedLibSource, SourceError
from deejayd.model import mediafilters

@jsonrpc_module(VideoSourceModule)
class VideoSource(_BaseSortedLibSource):
    SUBSCRIPTIONS = {
            "mediadb.mupdate": "cb_library_changes",
            }
    name = "video"
    base_medialist = "__videocurrent__"
    source_signal = 'video.update'
    sort_tags = ('title','rating','length')
    default_sorts = mediafilters.DEFAULT_VIDEO_SORT

    def __init__(self, db, library):
        super(VideoSource, self).__init__(db, library)
        # load saved
        try: ml_id = self.db.get_medialist_id(self.base_medialist, 'static')
        except ValueError: # medialist does not exist
            self._sorts = []
        else:
            self._sorts = list(self.db.get_magic_medialist_sorts(ml_id)) or []
            self._media_list.set(self._get_playlist_content(ml_id))
            self.set_sort(self._sorts)

    def set(self, value, type):
        need_sort = False
        if type == "directory":
            try: video_list = self.library.get_all_files(value)
            except NotFoundException:
                raise SourceError(_("Directory %s not found") % value)
            need_sort = True
        elif type == "search":
            sorts = self._sorts + self.__class__.default_sorts
            video_list = self.library.search_with_filter(\
                mediafilters.Contains("title",value), sorts)
        else:
            raise SourceError(_("type %s not supported") % type)

        self._media_list.set(video_list)
        if need_sort:
            self._media_list.sort(self._sorts + self.default_sorts)
        self.dispatch_signame(self.source_signal)

    def get_content(self, start = 0, length = None):
        stop = None
        if length is not None: 
            stop = start + int(length)
        return self._media_list.get(start, stop), None, self._sorts

    def close(self):
        super(VideoSource, self).close()
        # save panel sorts
        try: ml_id = self.db.get_medialist_id(self.base_medialist, 'static')
        except ValueError: # medialist does not exist
            pass
        else:
            self.db.set_magic_medialist_sorts(ml_id, self._sorts)

# vim: ts=4 sw=4 expandtab
