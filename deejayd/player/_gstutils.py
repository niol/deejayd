# Deejayd, a media player daemon
# Copyright (C) 2007-2017 Mickael Royer <mickael.royer@gmail.com>
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

import collections
from gi.repository import Gst
from deejayd.server.utils import str_decode


class TagListWrapper(collections.Mapping):

    def __init__(self, taglist, merge=False):
        self._list = taglist
        self._merge = merge

    def __len__(self):
        return self._list.n_tags()

    def __iter__(self):
        for i in xrange(len(self)):
            yield self._list.nth_tag_name(i)

    def __getitem__(self, key):
        if not Gst.tag_exists(key):
            raise KeyError

        values = []
        index = 0
        while 1:
            value = self._list.get_value_index(key, index)
            if value is None:
                break
            values.append(value)
            index += 1

        if not values:
            raise KeyError

        if self._merge:
            try:
                return " - ".join(values)
            except TypeError:
                return values[0]

        return values


def parse_gstreamer_taglist(tags):
    """Takes a GStreamer taglist and returns a dict containing only
    numeric and unicode values and str keys."""

    merged = {}
    for key in tags.keys():
        value = tags[key]
        # extended-comment sometimes containes a single vorbiscomment or
        # a list of them ["key=value", "key=value"]
        if key == "extended-comment":
            if not isinstance(value, list):
                value = [value]
            for val in value:
                if not isinstance(val, unicode):
                    continue
                split = val.split("=", 1)
                sub_key = str_decode(split[0])
                val = split[-1]
                if sub_key in merged:
                    if val not in merged[sub_key].split("\n"):
                        merged[sub_key] += "\n" + val
                else:
                    merged[sub_key] = val
        elif isinstance(value, Gst.DateTime):
            value = value.to_iso8601_string()
            merged[key] = value
        else:
            if isinstance(value, str):
                value = str_decode(value)

            if not isinstance(value, unicode) and \
                    not isinstance(value, (int, long, float)):
                value = unicode(value)

            merged[key] = value

    return merged
