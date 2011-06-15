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

from deejayd import DeejaydError, mediafilters
from deejayd.playlist import _Playlist

class MagicPlaylist(_Playlist):

    def content(self, first=0, length=-1):
        properties = dict(self.db.get_magic_medialist_properties(self.pl_id))
        if properties["use-or-filter"] == "1":
            filter = mediafilters.Or()
        else:
            filter = mediafilters.And()
        if properties["use-limit"] == "1":
            sort = [(properties["limit-sort-value"],\
                     properties["limit-sort-direction"])]
            limit = int(properties["limit-value"])
        else:
            sort, limit = [], None
        filter.filterlist = self.db.get_magic_medialist_filters(self.pl_id)
        songs = self.library.search_with_filter(filter, sort, limit)
        last = length == -1 and len(songs) or int(first) + int(length)
        return (songs[int(first):last], filter, None)

    def add_filter(self, filter):
        if filter.type != "basic":
            raise DeejaydError(\
                    _("Only basic filters are allowed for magic playlist"))
        self.db.add_magic_medialist_filters(self.pl_id, [filter])

    def remove_filter(self, filter):
        record_filters = self.db.get_magic_medialist_filters(self.pl_id)
        new_filters = []
        for record_filter in record_filters:
            if not filter.equals(record_filter):
                new_filters.append(record_filter)
        self.db.set_magic_medialist_filters(self.name, new_filters)

    def clear_filter(self):
        self.db.set_magic_medialist_filters(self.name, [])

    def get_properties(self):
        return dict(self.db.get_magic_medialist_properties(self.pl_id))

    def set_property(self, key, value):
        self.db.set_magic_medialist_property(self.pl_id, key, value)

# vim: ts=4 sw=4 expandtab
