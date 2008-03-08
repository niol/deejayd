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

extensions = [".flac"]
try: from mutagen.flac import FLAC
except ImportError:
    extensions = []

class FlacFile:
    supported_tag = ("tracknumber","title","genre","artist","album","date",\
                     "replaygain_track_gain", "replaygain_track_peak")

    def parse(self, file):
        infos = {}
        flac_info = FLAC(file)
        try: infos["bitrate"] = int(flac_info.info.bitrate)
        except AttributeError: infos["bitrate"] = 0
        infos["length"] = int(flac_info.info.length)

        for t in self.supported_tag:
            try: infos[t] = flac_info[t][0]
            except: infos[t] = '';

        return infos

object = FlacFile

# vim: ts=4 sw=4 expandtab
