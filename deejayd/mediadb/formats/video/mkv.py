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
from deejayd.mediadb.formats._base import _VideoFile
from deejayd.mediadb.formats.video import fault_tolerant
extensions = (".mkv",)

class VideoMKVFile(_VideoFile):
    mime_type = (u"video/x-matroska",)

    def extract(self, parser):
        for segment in parser.array("Segment"):
            self.__process_segment(segment)

    def __process_segment(self, segment):
        for field in segment:
            if field.name.startswith("Info["):
                self.__process_info(field)
            elif field.name.startswith("Tracks["):
                self.__process_tracks(field)
            elif field.name.startswith("Cluster["):
                return

    def __process_info(self, info):
        if "Duration/float" in info \
        and "TimecodeScale/unsigned" in info \
        and 0 < info["Duration/float"].value:
            try:
                self.infos["length"] = int(info["Duration/float"].value\
                     * info["TimecodeScale/unsigned"].value * 1e-9)
            except OverflowError:
                # long int too large to convert to int
                pass

    @fault_tolerant
    def __process_tracks(self, tracks):
        for track in tracks:
            if "TrackType/enum" not in track: continue
            if track["TrackType/enum"].display == "video":
                self.video.append({\
                    "height": track["Video/PixelHeight/unsigned"].value,\
                    "width": track["Video/PixelWidth/unsigned"].value})
            elif track["TrackType/enum"].display == "audio":
                self.audio.append({})
            elif track["TrackType/enum"].display == "subtitle":
                self.sub.append({})

object = VideoMKVFile

# vim: ts=4 sw=4 expandtab
