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

import os, datetime
from deejayd.mediadb.formats._base import _VideoFile
from deejayd.mediadb.formats.video import fault_tolerant
extensions = (".mp4", ".mov", ".m4v")

class VideoMP4File(_VideoFile):
    mime_type = (u'video/quicktime', u'video/mp4')

    def extract(self, parser):
        for atom in parser:
            if "movie" in atom:
                self.__process_movie(atom["movie"])

    def __process_movie(self, atom):
        for field in atom:
            if "movie_hdr" in field:
                self.__process_movie_header(field["movie_hdr"])
            if "track" in field:
                self.__process_track(field["track"])

    @fault_tolerant
    def __process_movie_header(self, hdr):
        duration = datetime.timedelta(seconds=float(hdr["duration"].value)\
                / hdr["time_scale"].value)
        self.infos["length"] = self._format_duration(duration)

    def __process_track(self, atom):
        # first try to get track type
        track_type = None
        for field in atom:
            if "media" in field:
                track_type = self.__get_track_type(field["media"])
                break

        if track_type != None:
            for field in atom:
                if "track_hdr" in field:
                    self.__process_track_header(field["track_hdr"], track_type)

    @fault_tolerant
    def __get_track_type(self, media):
        for field in media:
            if "hdlr" in field:
                return str(field["hdlr"]["subtype"].value)
        return None

    @fault_tolerant
    def __process_track_header(self, hdr, type):
        if type.find("vide") != -1: # video
            self.video.append({"height": int(hdr["frame_size_height"].value),\
                    "width": int(hdr["frame_size_width"].value),\
                    "id": hdr["track_id"].value})
        elif type.find("soun") != -1: # audio
            self.audio.append({"id": hdr["track_id"].value})
        elif type.find("text"): # subtitle
            self.sub.append({"id": hdr["track_id"].value})

object = VideoMP4File

# vim: ts=4 sw=4 expandtab
