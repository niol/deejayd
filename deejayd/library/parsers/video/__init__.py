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
import itertools
import time
from deejayd.server.utils import quote_uri
from deejayd.library.parsers import ParseError, NoParserError
from deejayd.db.connection import Session
from deejayd.db.models import AudioChannel, SubtitleChannel
from deejayd.db.models import LibraryFolder, Video

__all__ = ["VideoParserFactory"]

PARSERS = [
    ('asf', ['video/asf'], ['.asf', '.wmv', '.wma']),
    ('flv', ['video/flv'], ['.flv']),
    (
        'mkv', 
        ['video/x-matroska', 'application/mkv'], 
        ['.mkv', '.mka', '.webm']
    ),
    (
        'mp4', 
        ['video/quicktime', 'video/mp4'], 
        ['.mov', '.qt', '.mp4', '.mp4a', '.3gp', '.3gp2', '.3g2',
         '.mk2', '.m4v']
    ),
    ('mpeg', ['video/mpeg'], ['.mpeg', '.mpg', '.mp4', '.ts']),
    ('ogm', ['application/ogg'], ['.ogm', '.ogg', '.ogv']),
    ('riff', ['video/avi'], ['.wav', '.avi'])
]


class VideoParserFactory(object):
    subtitle_ext = (".srt",)

    def __init__(self, library):
        self.library = library
        self.extensions = set(itertools.chain(*[p[2] for p in PARSERS]))

    def get_extensions(self):
        return self.extensions

    def _format_title(self, f):
        (filename, ext) = os.path.splitext(f)
        title = filename.replace(".", " ")
        title = title.replace("_", " ")
        return title.title()

    def parse(self, file_obj, session):
        path = file_obj.get_path().encode("utf-8")
        extension = os.path.splitext(path)[1]
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
        mod = __import__(parser, globals=globals(), locals=locals(), 
                         fromlist=[], level=-1)
        with open(path, 'rb') as f:
            infos = mod.Parser(f)
            if infos:
                infos._finalize()
        if infos is None:
            raise ParseError(_("Video media %s not supported") % file)
        if len(infos["video"]) == 0:
            raise ParseError(_("This file is not a video"))
        # update video object
        f_infos = {
            "uri": quote_uri(path),
            "title": self._format_title(os.path.basename(path)),
            "length": int(infos["length"] or 0),
            "width": infos["video"][0]["width"],
            "height": infos["video"][0]["height"],
            "playing_state": {
                "zoom": 100,
                "aspect-ratio": "auto",
                "av-offset": 0,
                "sub-offset": 0,
                "current-audio": 0,
                "current-sub": 0,
            }
        }
        for k in f_infos:
            setattr(file_obj, k, f_infos[k])
        file_obj.last_modified = int(time.time())
        # set audio and subtitle channels
        map(file_obj.audio_channels.remove, file_obj.audio_channels)
        for idx, a_channel in enumerate(infos["audio"]):
            lang = a_channel.get("language", "Unknown") 
            ch_obj = AudioChannel(lang=lang, c_idx=idx+1)
            file_obj.audio_channels.append(ch_obj)
        map(file_obj.sub_channels.remove, file_obj.sub_channels)
        for idx, s_channel in enumerate(infos["subtitles"]):
            lang = s_channel.get("language", "Unknown") 
            ch_obj = SubtitleChannel(lang=lang, c_idx=idx+1)
            file_obj.sub_channels.append(ch_obj)

        return self.extra_parse(file_obj)

    def extra_parse(self, file_obj):
        path = file_obj.get_path().encode("utf-8")
        # find external subtitle
        base_path = os.path.splitext(path)[0]
        sub = ""
        for ext_type in self.subtitle_ext:
            if os.path.isfile(os.path.join(base_path + ext_type)):
                sub = quote_uri(base_path + ext_type)
                break

        file_obj.external_subtitle = sub
        return file_obj

    def inotify_extra_parse(self, file_path):
        if self.__is_subtitle(file_path):
            file_obj = self.__find_video(file_path)
            if file_obj is not None:
                file_obj.external_subtitle = quote_uri(file_path)
                return True
        return False

    def inotify_extra_remove(self, file_path):
        if self.__is_subtitle(file_path):
            file_obj = self.__find_video(file_path)
            if file_obj is not None:
                file_obj.external_subtitle = ""
                return True
        return False

    def __is_subtitle(self, file_path):
        name, ext = os.path.splitext(file_path)
        return ext in self.subtitle_ext

    def __find_video(self, sub_path):
        path, fn = os.path.split(sub_path)
        sub_name, ext = os.path.splitext(fn)

        dir_obj = self.library._get_folder(path)
        if dir_obj is not None:
            return Session.query(Video)\
                          .join(LibraryFolder)\
                          .filter(Video.folder == dir_obj)\
                          .filter(Video.filename.ilike(sub_name+".%"))\
                          .one_or_none()

        return None
