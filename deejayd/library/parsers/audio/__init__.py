# Deejayd, a media player daemon
# Copyright (C) 2007-2017 Mickael Royer <mickael.royer@gmail.com>
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
import glob
import time
from deejayd.db.models import Album, Song
from deejayd.db.connection import Session
from deejayd.library.parsers import NoParserError

__all__ = ["AudioParserFactory"]


class AudioParserFactory(object):

    def __init__(self, library):
        self.library = library

        base = os.path.dirname(__file__)
        base_import = "deejayd.library.parsers.audio"
        self.parsers = {}

        modules = [os.path.basename(f[:-3])
                   for f in glob.glob(os.path.join(base, "[!_]*.py"))]
        for m in modules:
            mod = __import__(base_import + "." + m, {}, {}, base)
            try:
                filetype_class = mod.object
            except AttributeError:
                continue
            for ext in mod.extensions:
                self.parsers[ext] = filetype_class()

    def get_extensions(self):
        return self.parsers.keys()

    def is_supported(self, filepath):
        extension = os.path.splitext(filepath)[1]
        return extension in self.parsers

    def parse(self, file_obj, session):
        path = file_obj.get_path()
        extension = os.path.splitext(path)[1]
        if extension not in self.parsers:
            raise NoParserError()
        infos = self.parsers[extension].parse(path.encode("utf-8"), 
                                              self.library)

        # find and save album
        album = session.query(Album)\
                       .filter(Album.name == infos["album"])\
                       .one_or_none()
        if album is None:
            album = Album(name=infos["album"], cover=None, 
                          cover_lmod=-1, cover_type=None)
            session.add(album)
        file_obj.album = album

        # update metadata
        for k in infos:
            if k not in ("album", "cover"):
                setattr(file_obj, k, infos[k])
        file_obj.last_modified = int(time.time())

        if "cover" in infos:
            c_infos = infos["cover"]
            album.update_cover(c_infos["data"], c_infos["mimetype"])
            return file_obj
        return self.extra_parse(file_obj, album=album)

    def extra_parse(self, file_obj, album=None):
        path = file_obj.get_path().encode('utf-8')
        if album is None:
            album = file_obj.album
        # find cover
        cover = CoverParser().find_cover(os.path.dirname(path))
        if cover is not None:
            need_update = os.stat(cover["path"]).st_mtime > album.cover_lmod
            if need_update:
                with open(cover["path"]) as c_data:
                    album.update_cover(c_data.read(), cover["mimetype"])
        else:
            album.erase_cover()

        return file_obj

    def inotify_extra_parse(self, filepath):
        CoverParser().parse(filepath, self.library)

    def inotify_extra_remove(self, filepath):
        CoverParser().remove(filepath, self.library)


class CoverParser(object):
    cover_name = ("cover.jpg", "folder.jpg", ".folder.jpg",
                  "cover.png", "folder.png", ".folder.png",
                  "albumart.jpg", "albumart.png")

    def remove(self, file, library):
        filename = os.path.basename(file)
        if filename in self.cover_name:
            dir_obj = library._get_folder(os.path.dirname(file))
            if dir_obj is not None:
                albums = Session.query(Album)\
                                .join(Song)\
                                .filter(Song.folder_id == dir_obj.id)\
                                .all()
                for album in albums:
                    album.erase_cover()

    def parse(self, file, library):
        filename = os.path.basename(file)
        if filename in self.cover_name:
            dir_obj = library._get_folder(os.path.dirname(file))
            if dir_obj is not None:
                mimetype = mimetypes.guess_type(file)
                albums = Session.query(Album)\
                                .join(Song)\
                                .filter(Song.folder_id == dir_obj.id)\
                                .all()
                with open(file) as c_data:
                    data = c_data.read()
                    for album in albums:
                        album.update_cover(data, mimetype[0])

    def find_cover(self, dir):
        cover, mimetype = None, None
        for name in self.cover_name:
            cover = os.path.join(dir, name)
            if os.path.isfile(cover):
                mimetype = mimetypes.guess_type(cover)
                return {"path": cover, "mimetype": mimetype[0]}
        return None
