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
from deejayd.utils import quote_uri

class _MediaFile:
    type = "unknown"

    def parse(self, file_path):
        return {
            "filename": os.path.basename(file_path),
            "uri": quote_uri(file_path),
            "type": self.type,
            "rating": "2", # [0-4]
            "lastplayed": "0",
            "skipcount": "0",
            "playcount": "0",
            }


class _AudioFile(_MediaFile):
    _tagclass_ = None
    type = "song"
    supported_tag = ("tracknumber","title","genre","artist","album","date",\
                     "replaygain_track_gain", "replaygain_track_peak")

    def _format_tracknumber(self, tckn):
        numbers = tckn.split("/")
        try: numbers = ["%02d" % int(num) for num in numbers]
        except (TypeError, ValueError):
            return tckn

        return "/".join(numbers)

    def parse(self, file):
        infos = _MediaFile.parse(self, file)
        if self._tagclass_:
            tag_info = self._tagclass_(file)
            for i in ("bitrate", "length"):
                try: infos[i] = int(getattr(tag_info.info, i))
                except AttributeError:
                    infos[i] = 0
            for t in self.supported_tag:
                try: info = tag_info[t][0]
                except:
                    info = ''
                if t == "tracknumber":
                    info = self._format_tracknumber(info)
                infos[t] = info
            # get front cover album if available
            infos["various_artist"] = infos["artist"]
            cover = self.get_cover(tag_info)
            if cover: infos["cover"] = cover

        return infos

class _VideoFile(_MediaFile):
    type = "video"

# vim: ts=4 sw=4 expandtab
