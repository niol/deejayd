# Deejayd, a media player daemon
# Copyright (C) 2007-2013 Mickael Royer <mickael.royer@gmail.com>
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

import shutil
import time
import os
from collections import MutableMapping

from deejayd.model.media_item import AudioItem, VideoItem
from deejayd.database.querybuilders import LibrarySelectQuery, ComplexSelect
from deejayd.database.querybuilders import SimpleSelect
from deejayd.database.querybuilders import DeleteQuery, EditRecordQuery
from deejayd.ui.config import DeejaydConfig
from deejayd.ui import log
from deejayd import Singleton, DeejaydError

DIR_TABLE = "library_dir"

class LibraryDir(object):

    def __init__(self, library, path, db_id=None, parent_id=None):
        self.path = path
        self.library = library
        self.db_id = db_id
        self.parent_id = parent_id
        self.parent = None

    def __strip_root(self, path):
        path = path.replace(self.library.get_root_path(), "")
        return path.lstrip("/")

    def to_json(self, subdirs=False, files=False):
        rs = {
            "id": self.db_id,
            "parent_id": self.get_parentid(),
            "name": os.path.basename(self.path),
            "path": self.path,
            "root": self.__strip_root(self.path),
        }
        if files:
            rs["files"] = self.get_files()
        if subdirs:
            rs["directories"] = map(lambda d: d.to_json(), self.get_subdirs())
        return rs

    def set_parent(self, parent):
        self.parent = parent

    def get_id(self):
        return self.db_id

    def get_parentid(self):
        if self.parent_id is not None:
            return self.parent_id
        elif self.parent is not None:
            return self.parent.get_id()
        return None

    def get_path(self):
        return self.path

    def get_subdirs(self):
        rs = SimpleSelect(DIR_TABLE) \
                    .select_column("id") \
                    .append_where("parent_id = %s", self.db_id) \
                    .execute()
        return self.library.get_dirs_with_ids([id for (id,) in rs])

    def get_files(self):
        if self.db_id is not None:
            f_ids = SimpleSelect(self.library.LIB_TABLE) \
                        .select_column("id") \
                        .append_where("directory=%s", self.db_id) \
                        .execute()
            return self.library.get_files_with_ids(map(lambda i: i[0], f_ids))
        return []

    def get_all_files(self):
        f_ids = ComplexSelect(self.library.LIB_TABLE) \
                    .join(DIR_TABLE, "%s.id = %s.directory" \
                        % (DIR_TABLE, self.library.LIB_TABLE)) \
                    .select_column("id") \
                    .append_where(DIR_TABLE + ".name LIKE %s", self.path + u"%%") \
                    .execute()
        files = self.library.get_files_with_ids(map(lambda i: i[0], f_ids))
        return files

    def save(self):
        if self.db_id is None:
            self.db_id = EditRecordQuery(DIR_TABLE) \
                            .add_value("name", self.path) \
                            .add_value("parent_id", self.get_parentid()) \
                            .add_value("lib_type", self.library.TYPE) \
                            .execute(commit=False)
            self.library.loaded_dirs[self.db_id] = self


    def erase(self, purge_files=False):
        if self.db_id is not None:
            if purge_files:
                map(lambda f: f.erase(), self.get_files())
            DeleteQuery(DIR_TABLE).append_where("id = %s", (self.db_id,)) \
                                  .execute(commit=False)
            map(lambda d: d.erase(purge_files), self.get_subdirs())
            try: del self.library.loaded_dirs[self.db_id]
            except KeyError:
                pass

class _Library(object):
    MEDIA_OBJECT = None
    TYPE = ""
    DIR_TABLE = "library_dir"
    LIB_TABLE = ""

    def __init__(self):
        self.root_path = None
        self.loaded_dirs = {}
        self.loaded_files = {}
        # load dirs and files
        result = SimpleSelect(DIR_TABLE) \
                    .select_column("name", "id", "parent_id") \
                    .append_where("lib_type = %s", self.TYPE) \
                    .execute()
        for d in result:
            self.loaded_dirs[int(d[1])] = LibraryDir(self, *d)

        query = self._build_library_query()
        for m in query.execute():
            self.loaded_files[m[3]] = self._map_media(m)

    def set_root_path(self, path):
        self.root_path = path

    def get_root_path(self):
        return self.root_path

    def get_dir_with_path(self, path, create=False):
        rs = SimpleSelect(DIR_TABLE) \
                    .select_column("id") \
                    .append_where("name = %s", path) \
                    .append_where("lib_type = %s", self.TYPE) \
                    .execute(expected_result="fetchone")
        db_id = rs and rs[0] or None
        if db_id is None:
            if not create:
                raise DeejaydError
            return LibraryDir(self, path)

        return self.get_dirs_with_ids((db_id,))[0]

    def get_dirs_with_ids(self, dir_ids):
        return [self.loaded_dirs[int(id)] for id in dir_ids]

    def get_file_with_path(self, dir_obj, filename, create=False,\
                           raise_ex=True):
        rs = ComplexSelect(self.LIB_TABLE) \
                    .join(DIR_TABLE, "%s.id = %s.directory" \
                        % (DIR_TABLE, self.LIB_TABLE)) \
                    .select_column("id") \
                    .append_where(DIR_TABLE + ".name = %s", dir_obj.get_path()) \
                    .append_where(self.LIB_TABLE + ".filename = %s", filename) \
                    .execute(expected_result="fetchone")
        db_id = rs and rs[0] or None
        if db_id is None:
            if not create:
                if raise_ex:
                    raise DeejaydError
                return None
            return self.MEDIA_OBJECT(self, dir_obj, filename)
        return self.get_files_with_ids((db_id,))[0]

    def get_files_with_ids(self, file_ids):
        return [self.loaded_files[int(id)] for id in file_ids]

    def list_tags(self, tag, ft):
        query = self._build_library_query(attrs=(tag,), map_media=False)
        if ft is not None:
            ft.restrict(query)
        query.order_by_tag(tag)
        return query.execute()

    def search(self, ft, orders=[], limit=None):
        query = self._build_library_query(attrs=["id"], map_media=False)
        ft.restrict(query)
        for (tag, direction) in orders:
            descending = direction == "descending"
            query.order_by_tag(tag, descending=descending)
        query.set_limit(limit)
        return [self.loaded_files[m[0]] for m in query.execute()]

    def clean_library(self, path, dir_ids, file_ids):
        d_ids = SimpleSelect(DIR_TABLE) \
                    .select_column("id") \
                    .append_where("name LIKE %s", path + u"%%") \
                    .append_where("id NOT IN (%s)" % ",".join(map(str, dir_ids))) \
                    .append_where("lib_type = %s", self.TYPE) \
                    .execute()
        map(lambda d: d.erase(), self.get_dirs_with_ids([d[0] for d in d_ids]))

        f_ids = ComplexSelect(self.LIB_TABLE) \
            .join(DIR_TABLE, "%s.id = %s.directory" % (DIR_TABLE, self.LIB_TABLE)) \
            .select_column("id") \
            .append_where(DIR_TABLE + ".name LIKE %s", path + u"%%") \
            .append_where(self.LIB_TABLE + ".id NOT IN (%s)" % ",".join(map(str, file_ids))) \
            .append_where(DIR_TABLE + ".lib_type = %s", (self.TYPE,)) \
            .execute()
        map(lambda f: f.erase(), self.get_files_with_ids([f[0] for f in f_ids]))

    def get_media_attributes(self):
        return self.MEDIA_OBJECT.attributes()

    def _map_media(self, db_result):
        dir_id = db_result[0]

        media_id = db_result[3]
        media_name = db_result[4]
        return self.MEDIA_OBJECT(self, self.loaded_dirs[dir_id],
                                 media_name, db_id=media_id,
                                 infos=db_result[5:])

    def _build_library_query(self, attrs=None, map_media=True):
        attrs = attrs or self.MEDIA_OBJECT.attributes()
        query = LibrarySelectQuery(self.LIB_TABLE, self.DIR_TABLE)
        if map_media:
            query.select_dir()
            map(lambda a: query.select_column(a), ("id", "filename"))
        for tag in attrs:
            query.select_tag(tag)
        return query

class Album(MutableMapping):
    COVER_EXT = {
        "image/jpeg": "jpg",
        "image/png": "png",
    }

    def __init__(self, library, name, cover_lmod= -1,
                 cover_type=None, compilation=0, db_id=None):
        self.library = library
        self.db_id = db_id
        self.dirty = False
        self.data = {
            "album": name,
            "compilation": compilation,
            "cover_lmod": cover_lmod,
            "cover_type": cover_type,
        }

    def __getitem__(self, key):
        if key == "id":
            return self.db_id
        return self.data[key]

    def __setitem__(self, key, value):
        if key == "id":
            raise DeejaydError("id can't be modified")
        self.dirty = True
        self.data[key] = value

    def __delitem__(self, key):
        raise DeejaydError("key can't be removed from album object")

    def __iter__(self):
        return self.data.iterkeys()

    def __len__(self):
        return len(self.data)

    def update_cover(self, orig_path, mimetype):
        dest = os.path.join(self.library.get_cover_folder(),
                            self.get_cover_filename(cover_type=mimetype))
        try: shutil.copy(orig_path, dest)
        except OSError:
            log.err(_("Unable to copy cover to correct folder"))
            return
        self.update({
            "cover_type": mimetype,
            "cover_lmod": time.time()
        })
        self.save()

    def get_cover_filename(self, cover_type = None):
        cover_type = cover_type or self.data["cover_type"]
        if cover_type is not None and self.db_id is not None:
            return "%s.%s" % (self.db_id, self.COVER_EXT[cover_type])
        return ""

    def to_json(self):
        return {
            "id": self.db_id,
            "name": self.data["album"],
            "cover_filename": self.get_cover_filename(),
        }

    def erase(self):
        if self.db_id is not None:
            DeleteQuery(self.library.ALBUM_TABLE) \
                    .append_where("id = %s", (self.db_id,)) \
                    .execute(commit=False)
            # delete cover
            c_path = os.path.join(self.library.get_cover_folder(),
                                  self.get_cover_filename())
            if os.path.isfile(c_path):
                try: os.unlink(c_path)
                except OSError, err:
                    log.err(_("Unable to remove cover %s: %s") \
                            % (self.get_cover_filename(), err))

    def save(self):
        if self.db_id is None or self.dirty:
            query = EditRecordQuery(self.library.ALBUM_TABLE)
            for k,v in self.data.items():
                query.add_value(k, v)
            if self.db_id is not None:
                query.set_update_id("id", self.db_id) \
                     .execute(commit=False)
            else:
                self.db_id = query.execute(commit=False)
                self.library.loaded_albums[self.db_id] = self
        self.dirty = False


class AudioLibrary(_Library):
    MEDIA_OBJECT = AudioItem
    TYPE = "audio"
    LIB_TABLE = "song"
    ALBUM_TABLE = "album"
    loaded_albums = {}

    def __init__(self):
        self.cover_folder = DeejaydConfig().get("mediadb", "cover_directory")
        if not os.path.exists(self.cover_folder):
            try: os.mkdir(self.cover_folder, 0755)
            except OSError, err:
                raise DeejaydError(_("Unable to create cover folder %s: %s")
                                   % (self.cover_folder, err))
        # load albums
        alb_entries = SimpleSelect(self.ALBUM_TABLE) \
            .select_column("id", "album", "cover_lmod",
                           "cover_type", "compilation") \
            .execute()
        for (id, album, cover_lmod, cover_type, compil) in alb_entries:
            self.loaded_albums[id] = Album(self, album, db_id=id,
                                           cover_lmod=cover_lmod,
                                           cover_type=cover_type,
                                           compilation=compil)
        super(AudioLibrary, self).__init__()

    def get_album_with_name(self, name, create=False):
        album_entry = SimpleSelect(self.ALBUM_TABLE) \
                            .select_column("id") \
                            .append_where("album = %s", name) \
                            .execute(expected_result="fetchone")
        db_id = album_entry and album_entry[0] or None
        if db_id is None:
            if not create:
                raise DeejaydError
            return Album(self, name)
        return self.loaded_albums[db_id]

    def get_album_with_id(self, id):
        try: return self.loaded_albums[id]
        except KeyError:
            raise DeejaydError(_("Album with id %d not found") % id)

    def get_albums_with_filter(self, filter):
        query = LibrarySelectQuery(self.LIB_TABLE, self.DIR_TABLE) \
                        .order_by_tag("album") \
                        .select_column("id", self.ALBUM_TABLE)
        if filter is not None:
            filter.restrict(query)
        a_ids = query.execute()
        return map(lambda id: self.loaded_albums[id[0]], a_ids)

    def get_cover_folder(self):
        return self.cover_folder

    def clean_library(self, path, dir_ids, file_ids):
        super(AudioLibrary, self).clean_library(path, dir_ids, file_ids)
        # clean album
        used_album = SimpleSelect(self.LIB_TABLE) \
                            .select_column("album_id")
        unused_albums = SimpleSelect(self.ALBUM_TABLE) \
                .select_column("id") \
                .append_where("id NOT IN (%s)" % used_album.to_sql()) \
                .execute()
        map(lambda a_id: self.loaded_albums[a_id[0]].erase(), unused_albums)

    def _build_library_query(self, attrs=None, map_media=True):
        query = super(AudioLibrary, self)._build_library_query(attrs, map_media)
        return query.join_on_tag("album")

class VideoLibrary(_Library):
    MEDIA_OBJECT = VideoItem
    TYPE = "video"
    LIB_TABLE = "video"


@Singleton
class LibraryFactory(object):
    __loaded = {}

    def get_audio_library(self):
        if "audio" not in self.__loaded:
            self.__loaded["audio"] = AudioLibrary()
        return self.__loaded["audio"]

    def get_video_library(self):
        if "video" not in self.__loaded:
            self.__loaded["video"] = VideoLibrary()
        return self.__loaded["video"]

# vim: ts=4 sw=4 expandtab
