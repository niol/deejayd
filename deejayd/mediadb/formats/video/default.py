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
extensions = (".avi", ".asf", ".wmv", ".ogm", ".mkv", ".mp4", ".mov", ".m4v")

class VideoFile(_VideoFile):
    mime_type = (u"video/x-msvideo", u"video/x-ms-asf", u"video/x-ms-wmv",\
            u"video/x-ogg", u"video/x-theora",u"application/ogg",\
            u"video/x-matroska", u'video/quicktime', u'video/mp4')

object = VideoFile

# vim: ts=4 sw=4 expandtab
