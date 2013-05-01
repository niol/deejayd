# Deejayd, a media player daemon
# Copyright (C) 2013 Mickael Royer <mickael.royer@gmail.com>
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
import mimetypes
from deejayd.utils import quote_uri
from deejayd import DeejaydError
from deejayd.mediadb.parsers import ParseError, NoParserError

__all__ = ["VideoParserFactory"]

PARSERS = [('asf', ['video/asf'], ['asf', 'wmv', 'wma']),
           ('flv', ['video/flv'], ['flv']),
           ('mkv', ['video/x-matroska', 'application/mkv'], ['mkv', 'mka', 'webm']),
           ('mp4', ['video/quicktime', 'video/mp4'], ['mov', 'qt', 'mp4', 'mp4a', '3gp', '3gp2', '3g2', 'mk2']),
           ('mpeg', ['video/mpeg'], ['mpeg', 'mpg', 'mp4', 'ts']),
           ('ogm', ['application/ogg'], ['ogm', 'ogg', 'ogv']),
           ('riff', ['video/avi'], ['wav', 'avi'])
]

class VideoParserFactory(object):

    def get_extensions(self):
        return (".avi", ".flv", ".asf", ".wmv", ".ogm", ".mkv", \
                ".mp4", ".mov", ".m4v")

    def _format_title(self, f):
        (filename, ext) = os.path.splitext(f)
        title = filename.replace(".", " ")
        title = title.replace("_", " ")
        return title.title()

    def parse(self, path):
        extension = os.path.splitext(path)[1][1:]
        mimetype = mimetypes.guess_type(path)[0]
        parser_ext = None
        parser_mime = None
        for (parser_name, parser_mimetypes, parser_extensions) in PARSERS:
            if mimetype in parser_mimetypes:
                parser_mime = parser_name
            if extension in parser_extensions:
                parser_ext = parser_name
        parser = parser_mime or parser_ext
        if not parser:
            raise NoParserError()
        mod = __import__(parser, globals=globals(), locals=locals(), fromlist=[], level= -1)
        with open(path, 'rb') as f:
            infos = mod.Parser(f)
            if infos:
                infos._finalize()
        if infos is None:
            raise ParseError(_("Video media %s not supported") % file)
        if len(infos["video"]) == 0:
            raise ParseError(_("This file is not a video"))

        return {
            "filename": os.path.basename(path),
            "uri": quote_uri(path),
            "type": "video",
            "rating": "2",  # [0-4]
            "lastplayed": "0",
            "skipcount": "0",
            "playcount": "0",
            "title": self._format_title(os.path.basename(path)),
            "length": int(infos["length"] or 0),
            "videowidth": infos["video"][0]["width"],
            "videoheight": infos["video"][0]["height"],
            "audio_channels": len(infos["audio"]),
            "subtitle_channels": len(infos["subtitles"]),
        }

# vim: ts=4 sw=4 expandtab
