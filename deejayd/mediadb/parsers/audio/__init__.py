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
import mimetypes
import glob
from deejayd.server.utils import quote_uri
from deejayd import DeejaydError
from deejayd.mediadb.parsers import ParseError, NoParserError

__all__ = ["AudioParserFactory"]

class AudioParserFactory(object):

    def __init__(self, library):
        self.library = library

        base = os.path.dirname(__file__)
        base_import = "deejayd.mediadb.parsers.audio"
        self.parsers = {}

        modules = [os.path.basename(f[:-3]) \
                    for f in glob.glob(os.path.join(base, "[!_]*.py"))]
        for m in modules:
            mod = __import__(base_import + "." + m, {}, {}, base)
            try: filetype_class = mod.object
            except AttributeError:
                continue
            for ext in mod.extensions:
                self.parsers[ext] = filetype_class()

    def parse(self, file_obj):
        path = file_obj.get_path()
        extension = os.path.splitext(path)[1]
        if extension not in self.parsers:
            raise NoParserError()
        infos = self.parsers[extension].parse(path, self.library)

        # find and save album
        library_model = self.library.get_model()
        album = library_model.get_album_with_name(infos["album"], create=True)
        album.save()
        file_obj.set_album(album)

        # update metadata
        for k in infos:
            if k not in ("album", "cover"):
                file_obj[k] = infos[k]

        if "cover" in infos:
            tmp_path = os.path.join("/tmp", "djd_tmp_cover")
            with open(tmp_path, "w") as f:
                f.write(infos["cover"]["data"])
            album.update_cover(tmp_path, infos["cover"]["mimetype"])
            os.unlink(tmp_path)
            return file_obj
        return self.extra_parse(file_obj, album=album)

    def extra_parse(self, file_obj, album=None):
        path = file_obj.get_path()
        if album is None:
            album = file_obj.get_album()
        # find cover
        cover = CoverParser().find_cover(os.path.dirname(path))
        if cover is not None:
            need_update = os.stat(cover["path"]).st_mtime > album["cover_lmod"]
            if need_update:
                album.update_cover(cover["path"], cover["mimetype"])
        else:
            album.erase_cover()

        return file_obj

    def inotify_extra_parse(self, filepath):
        CoverParser().parse(filepath, self.library)

    def inotify_extra_remove(self, filepath):
        CoverParser().remove(filepath, self.library)

class CoverParser(object):
    cover_name = ("cover.jpg", "folder.jpg", ".folder.jpg", \
                  "cover.png", "folder.png", ".folder.png", \
                  "albumart.jpg", "albumart.png")

    def remove(self, file, library):
        filename = os.path.basename(file)
        if filename in self.cover_name:
            lib_model = library.get_model()
            try:
                dir_obj = lib_model.get_dir_with_path(os.path.dirname(file))
            except DeejaydError:
                return
            for file_obj in dir_obj.get_files():
                file_obj.get_album().erase_cover()

    def parse(self, file, library):
        filename = os.path.basename(file)
        if filename in self.cover_name:
            lib_model = library.get_model()
            try:
                dir_obj = lib_model.get_dir_with_path(os.path.dirname(file))
            except DeejaydError:
                return

            mimetype = mimetypes.guess_type(file)
            for file_obj in dir_obj.get_files():
                file_obj.get_album().update_cover(file, mimetype[0])

    def find_cover(self, dir):
        cover, mimetype = None, None
        for name in self.cover_name:
            cover = os.path.join(dir, name)
            if os.path.isfile(cover):
                mimetype = mimetypes.guess_type(cover)
                return {"path": cover, "mimetype": mimetype[0]}
        return None

# vim: ts=4 sw=4 expandtab
