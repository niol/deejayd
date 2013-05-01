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

extensions = ['.mp4', '.m4a']
try: from mutagen.mp4 import MP4
except ImportError:
    extensions = []

class Mp4File(_AudioFile):
    __translate = {
        "\xa9nam": "title",
        "\xa9alb": "album",
        "\xa9ART": "artist",
        "\xa9day": "date",
        "\xa9gen": "genre",
        "----:com.apple.iTunes:replaygain_track_gain": "replaygain_track_gain",
        "----:com.apple.iTunes:replaygain_track_peak": "replaygain_track_peak",
        }
    __tupletranslate = {
        "trkn": "tracknumber",
        "disk": "discnumber",
        }

    def parse(self, file):
        infos = _AudioFile.parse(self, file)
        mp4_info = MP4(file)
        infos["bitrate"] = int(mp4_info.info.bitrate)
        infos["length"] = int(mp4_info.info.length)

        for tag, name in self.__translate.iteritems():
            try: infos[name] = mp4_info[tag][0]
            except: infos[name] = '';

        for tag, name in self.__tupletranslate.iteritems():
            try:
                cur, total = mp4_info[tag][0]
                if total: infos[name] = "%02d/%02d" % (cur, total)
                else: infos[name] = "%02d" % cur
            except: infos[name] = '';

        # extract cover
        try: cover = mp4_info["covr"][0]
        except (KeyError, ValueError):
            pass
        else:
            mime = "image/jpeg"
            if cover.format == cover.FORMAT_PNG:
                mime = "image/png"
            infos["cover"] = {"mime": mime, "data": cover}

        infos["various_artist"] = infos["artist"]
        return infos

object = Mp4File

# vim: ts=4 sw=4 expandtab
