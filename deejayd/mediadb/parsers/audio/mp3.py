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
from deejayd.mediadb.parsers.audio.core import _AudioFile

extensions = [".mp3", ".mp2", ".aac"]
try: from mutagen.mp3 import MP3
except ImportError:
    extensions = []


class Mp3File(_AudioFile):
    IDS = { "TIT2": "title",
            "TPE1": "artist",
            "TALB": "album",
            }

    def parse(self, file, library):
        self.__infos = _AudioFile.parse(self, file, library)
        mp3_info = MP3(file)

        self.__infos.update([
            ("title", ""),
            ("artist", ""),
            ("album", ""),
            ("tracknumber", ""),
            ("discnumber", ""),
            ("date", ""),
            ("genre", ""),
            ("replaygain_track_gain", ""),
            ("replaygain_track_peak", ""),
            ("replaygain_album_gain", ""),
            ("replaygain_album_peak", ""),
            ("length", int(mp3_info.info.length)),
            ])

        tag = mp3_info.tags
        if not tag:
            self.__infos["title"] = os.path.split(file)[1]
            return self.__infos

        for frame in tag.values():
            if frame.FrameID == "RVA2":  # replaygain
                self.__process_rg(frame)
                continue
            elif frame.FrameID == "TCON":  # genre
                self.__infos["genre"] = frame.genres[0]
                continue
            elif frame.FrameID == "TDRC":  # date
                list = [stamp.text for stamp in frame.text]
                self.__infos["date"] = list[0]
                continue
            elif frame.FrameID == "TRCK":  # tracknumber
                self.__infos["tracknumber"] = self._format_number(frame.text[0])
            elif frame.FrameID == "TPOS":  # discnumber
                self.__infos["discnumber"] = self._format_number(frame.text[0])
            elif frame.FrameID in self.IDS.keys():
                self.__infos[self.IDS[frame.FrameID]] = frame.text[0]
            elif frame.FrameID == "APIC":  # picture
                if frame.type == 3:  # album front cover
                    self.__infos["cover"] = {"data": frame.data,
                                      "mimetype": frame.mime}
            else: continue

        return self.__infos

    def __process_rg(self, frame):
        if frame.channel == 1 and frame.desc in ("track", "album"):
            self.__infos["replaygain_%s_gain" % frame.desc] = "%+f dB" % frame.gain
            self.__infos["replaygain_%s_peak" % frame.desc] = str(frame.peak)

object = Mp3File

# vim: ts=4 sw=4 expandtab