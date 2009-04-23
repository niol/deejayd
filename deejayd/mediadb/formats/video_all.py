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
# hachoir
from hachoir_core.error import HachoirError
from hachoir_parser import createParser
from hachoir_metadata import extractMetadata

from deejayd.mediadb.formats._base import _VideoFile
extensions = (".avi", ".mkv", ".asf", ".ogm", "mp4", )

class VideoFile(_VideoFile):

    def __format_title(self, f):
        (filename,ext) = os.path.splitext(f)
        title = filename.replace(".", " ")
        title = title.replace("_", " ")
        return title.title()

    def __format_duration(self, duration):
        return str(duration.days*86400 + duration.seconds)

    def parse(self, file):
        infos = _VideoFile.parse(self, file)
        (path,filename) = os.path.split(file)
        infos["title"] = self.__format_title(filename)

        # parse video file with hachoir
        parser = createParser(unicode(file))
        if not parser: # file not supported
            raise TypeError(_("Video media not supported by hachoir lib"))
        try: metadata = extractMetadata(parser)
        except HachoirError, err:
            raise TypeError(_("Metadata extraction error: %s") % unicode(err))
        if not metadata:
            raise TypeError(_("Hachoir don't succeed to extract metadata"))
        # verify if it is really a video
        mime_type = metadata.get("mime_type", "")
        if not mime_type.startswith("video"):
            raise TypeError(_("Wrong file mime type"))

        # extract infos
        infos["length"] = self.__format_duration(metadata.get("duration",\
                datetime.timedelta(0,0,0)))
        try:
            infos["videowidth"] = str(metadata.get("width"))
            infos["videoheight"] = str(metadata.get("height"))
        except ValueError:
            # resolution not found in the container, extract from video stream
            for group in metadata.iterGroups():
                if group.has("width") and group.has("height"):
                    infos["videowidth"] = str(group.get("width"))
                    infos["videoheight"] = str(group.get("height"))
                    break
        if "videoheight" not in infos.keys():
            raise TypeError(_("Unable to get resolution from this file"))

        return infos

object = VideoFile

# vim: ts=4 sw=4 expandtab
