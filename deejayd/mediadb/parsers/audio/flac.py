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

from deejayd.mediadb.parsers.audio.core import _AudioFile

extensions = [".flac"]
try: from mutagen.flac import FLAC
except ImportError:
    extensions = []

class FlacFile(_AudioFile):
    _tagclass_ = FLAC

    def get_cover(self, tag_info):
        for picture in tag_info.pictures:
            if picture.type == 3:  # album front cover
                return {"data": picture.data, "mime": picture.mime}
        return None

object = FlacFile

# vim: ts=4 sw=4 expandtab
