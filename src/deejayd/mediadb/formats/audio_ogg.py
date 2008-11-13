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

from deejayd.mediadb.formats._base import _AudioFile

extensions = [".ogg"]
try: from mutagen.oggvorbis import OggVorbis
except ImportError:
    extensions = []

class OggFile(_AudioFile):
    _tagclass_ = OggVorbis

    def get_cover(self, tag_info):
        if 'coverarttype' in tag_info.keys() and\
                int(tag_info['coverarttype'][0])==3:
            try:
                return {"data": tag_info['coverart'][0],\
                        "mime": tag_info['coverartmime'][0]}
            except KeyError:
                return None
        return None

object = OggFile

# vim: ts=4 sw=4 expandtab
