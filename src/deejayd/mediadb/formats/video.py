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

import os
extensions = [".avi", ".mpeg", ".mpg", ".mkv"]

class VideoFile:
    supported_tag = ("videowidth","length","videoheight")

    def __init__(self, player):
        self.player = player

    def parse(self, file):
        (path,filename) = os.path.split(file)
        def format_title(f):
            (filename,ext) = os.path.splitext(f)
            title = filename.replace(".", " ")
            title = title.replace("_", " ")

            return title.title()

        infos = self.parse_sub(file)
        infos["title"] = format_title(filename)
        video_info = self.player.get_video_file_info(file)
        for t in self.supported_tag:
            infos[t] = video_info[t]

        return infos

    def parse_sub(self, file):
        infos = {}
        # Try to find a subtitle (same name with a srt/sub extension)
        (base_path,ext) = os.path.splitext(file)
        sub = ""
        for ext_type in (".srt",".sub"):
            if os.path.isfile(base_path + ext_type):
                sub = "file://" + base_path + ext_type
                break
        infos["subtitle"] = sub
        return infos

object = VideoFile

# vim: ts=4 sw=4 expandtab
