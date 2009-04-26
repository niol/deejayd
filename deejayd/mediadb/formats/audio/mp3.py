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
from deejayd.mediadb.formats._base import _AudioFile

extensions = [".mp3",".mp2",".aac"]
try: from mutagen.mp3 import MP3
except ImportError:
    extensions = []


class Mp3File(_AudioFile):
    IDS = { "TIT2": "title",
            "TPE1": "artist",
            "TALB": "album",
            }
    replaygain_process = False

    def parse(self, file):
        infos = _AudioFile.parse(self, file)
        mp3_info = MP3(file)

        infos.update([
            ("title", ""),
            ("artist", ""),
            ("album", ""),
            ("tracknumber", ""),
            ("date", ""),
            ("genre", ""),
            ("replaygain_track_gain", ""),
            ("replaygain_track_peak", ""),
            ("bitrate", int(mp3_info.info.bitrate)),
            ("length", int(mp3_info.info.length)),
            ])

        tag = mp3_info.tags
        if not tag:
            infos["title"] = os.path.split(file)[1]
            return infos

        for frame in tag.values():
            if frame.FrameID == "TXXX":
                if frame.desc in ("replaygain_track_peak",\
                                  "replaygain_track_gain"):
                    # Some versions of Foobar2000 write broken Replay Gain
                    # tags in this format.
                    infos[frame.desc] = frame.text[0]
                    self.replaygain_process = True
                else: continue
            elif frame.FrameID == "RVA2": # replaygain
                self.__process_rg(frame, infos)
                continue
            elif frame.FrameID == "TCON": # genre
                infos["genre"] = frame.genres[0]
                continue
            elif frame.FrameID == "TDRC": # date
                list = [stamp.text for stamp in frame.text]
                infos["date"] = list[0]
                continue
            elif frame.FrameID == "TRCK": # tracknumber
                infos["tracknumber"] = self._format_tracknumber(frame.text[0])
            elif frame.FrameID in self.IDS.keys():
                infos[self.IDS[frame.FrameID]] = frame.text[0]
            elif frame.FrameID == "APIC": # picture
                if frame.type == 3: # album front cover
                    infos["cover"] = {"data": frame.data, "mime": frame.mime}
            else: continue

        infos["various_artist"] = infos["artist"]
        return infos

    def __process_rg(self, frame, infos):
        if frame.channel == 1:
            if frame.desc == "album": return # not supported
            elif frame.desc == "track" or not self.replaygain_process:
                infos["replaygain_track_gain"] = "%+f dB" % frame.gain
                infos["replaygain_track_peak"] = str(frame.peak)
                self.replaygain_process = True

object = Mp3File

# vim: ts=4 sw=4 expandtab
