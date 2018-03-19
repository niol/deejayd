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

from deejayd.library.parsers._base import _VideoFile


class VideoFile(_VideoFile):
    extensions = (".avi", ".asf", ".wmv", ".ogm", ".mkv", ".mp4", ".mov", ".m4v")
    mime_type = ("video/x-msvideo", "video/x-ms-asf", "video/x-ms-wmv",\
                 "video/x-ogg", "video/x-theora", "application/ogg",
                 "video/x-matroska", 'video/quicktime', 'video/mp4')


type = "main"
object = VideoFile

# vim: ts=4 sw=4 expandtab