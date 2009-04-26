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
from hachoir_metadata import extractMetadata

from deejayd.mediadb.formats._base import _VideoFile
extensions = (".avi", ".asf", ".wmv", ".ogm")

class VideoFile(_VideoFile):
    mime_type = (u"video/x-msvideo", u"video/x-ms-asf", u"video/x-ms-wmv",\
            u"video/x-ogg", u"video/x-theora",u"application/ogg")

    def extract(self, parser):
        try: metadata = extractMetadata(parser)
        except HachoirError, err:
            raise TypeError(_("Metadata extraction error: %s") % unicode(err))
        if not metadata:
            raise TypeError(_("Hachoir don't succeed to extract metadata"))

        # extract infos
        self.infos["length"] = self._format_duration(metadata.get("duration",\
                datetime.timedelta(0,0,0)))
        try:
            groups = getattr(metadata, "_MultipleMetadata__groups")
            for key, g_metadata in groups.iteritems():
                if key.startswith("video"):
                    width, height = 0, 0
                    try:
                        width = str(g_metadata.get("width"))
                        height = str(g_metadata.get("height"))
                    except ValueError:
                        pass
                    self.video.append({"width": width, "height": height})
                elif key.startswith("audio"):
                    self.audio.append({})
        except AttributeError: # Not multiple metadata element
            print "skip groups part"
            try:
                width = str(metadata.get("width"))
                height = str(metadata.get("height"))
            except ValueError:
                raise TypeError(_("Unable to get resolution from this file"))
            self.video.append({"width": width, "height": height})

object = VideoFile

# vim: ts=4 sw=4 expandtab
