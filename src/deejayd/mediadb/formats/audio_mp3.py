# Deejayd, a media player daemon
# Copyright (C) 2007 Mickael Royer <mickael.royer@gmail.com>
#                    Alexandre Rossi <alexandre.rossi@gmail.com>
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

extensions = [".mp3",".mp2"]
try:
    from mutagen.mp3 import MP3
    from mutagen.easyid3 import EasyID3
except ImportError:
    extensions = []


class Mp3File:
    supported_tag = ("tracknumber","title","genre","artist","album","date")

    def parse(self, file):
        infos = {}
        mp3_info = MP3(file, ID3=EasyID3)
        infos["bitrate"] = int(mp3_info.info.bitrate)
        infos["length"] = int(mp3_info.info.length)

        for t in self.supported_tag:
            try: infos[t] = mp3_info[t][0]
            except: infos[t] = '';

        return infos

object = Mp3File

# vim: ts=4 sw=4 expandtab
