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

class _MediaFile:
    type = "unknown"

    def __init__(self, player):
        self.player = player

    def parse(self, file_path):
        return {
            "type": self.type,
            }


class _AudioFile(_MediaFile):
    _tagclass_ = None
    type = "song"
    supported_tag = ("tracknumber","title","genre","artist","album","date",\
                     "replaygain_track_gain", "replaygain_track_peak")

    def parse(self, file):
        infos = _MediaFile.parse(self, file)
        if self._tagclass_:
            tag_info = self._tagclass_(file)
            for i in ("bitrate", "length"):
                try: infos[i] = int(getattr(tag_info.info, i))
                except AttributeError:
                    infos[i] = 0
            for t in self.supported_tag:
                try: infos[t] = tag_info[t][0]
                except:
                    infos[t] = ''

        return infos

class _VideoFile(_MediaFile):
    type = "video"

# vim: ts=4 sw=4 expandtab
