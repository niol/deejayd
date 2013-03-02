# Deejayd, a media player daemon
# Copyright (C) 2007-2013 Mickael Royer <mickael.royer@gmail.com>
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

from deejayd.jsonrpc.interfaces import VideoSourceModule, jsonrpc_module
from deejayd.mediadb.library import NotFoundException
from deejayd.sources._base import _BaseSortedLibSource, SourceError
from deejayd.utils import quote_uri
from deejayd.model import mediafilters

@jsonrpc_module(VideoSourceModule)
class VideoSource(_BaseSortedLibSource):
    SUBSCRIPTIONS = {
            "mediadb.mupdate": "cb_library_changes",
            }
    name = "video"
    base_medialist = "__videocurrent__"
    source_signal = 'video.update'
    sort_tags = ('title', 'rating', 'length')

    def __init__(self, db, library):
        super(VideoSource, self).__init__(db, library)
        self._media_list.load()

    def set(self, value, type):
        if type == "directory":
            # verify that this dir exists
            self.library.get_all_files(value)

            value = os.path.join(self.library.get_root_path(), value)
            uri = quote_uri(value)
            filter = mediafilters.StartsWith("uri", uri)
        elif type == "search":
            filter = mediafilters.Contains("title", value)
        else:
            raise SourceError(_("type %s not supported") % type)

        self._media_list.set_filters([filter])
        self.dispatch_signame(self.source_signal)

    def get_content(self, start=0, length=None):
        stop = None
        if length is not None:
            stop = start + int(length)
        return self._media_list.get(start, stop), \
            self._media_list.get_main_filter(), \
            self._media_list.get_sorts()

# vim: ts=4 sw=4 expandtab