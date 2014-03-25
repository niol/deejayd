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

import os
from deejayd.server.utils import quote_uri


class _AudioFile(object):
    _tagclass_ = None
    type = "song"
    supported_tag = ("tracknumber", "title", "genre", "artist", "album", \
            "discnumber", "date", "replaygain_track_gain", \
            "replaygain_track_peak", "replaygain_album_gain", \
            "replaygain_album_peak")

    def _format_number(self, nb):
        numbers = nb.split("/")
        try: numbers = ["%02d" % int(num) for num in numbers]
        except (TypeError, ValueError):
            return nb

        return "/".join(numbers)

    def parse(self, file, library):
        infos = {
            "uri": quote_uri(file),
            }
        if self._tagclass_:
            tag_info = self._tagclass_(file)
            try: infos["length"] = int(getattr(tag_info.info, "length"))
            except AttributeError:
                infos["length"] = 0
            for t in self.supported_tag:
                try: info = tag_info[t][0]
                except:
                    info = ''
                if t in ("tracknumber", "discnumber"):
                    info = self._format_number(info)
                infos[t] = info
            # get front cover album if available
            cover = self.get_cover(tag_info)
            if cover: infos["cover"] = cover

        return infos

# vim: ts=4 sw=4 expandtab
