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

import time
from zope.interface import implements

from deejayd.model._model import IObjectModel
from deejayd.model.media_item import AudioItem, VideoItem
from deejayd.database.querybuilders import LibrarySelectQuery, ComplexSelect
from deejayd.database.querybuilders import SimpleSelect
from deejayd.database.querybuilders import MediaSelectQuery
from deejayd.database.querybuilders import ReplaceQuery
from deejayd.database.querybuilders import DeleteQuery, EditRecordQuery
from deejayd import Singleton
from deejayd.database.connection import DatabaseConnection

class _Library(object):
    implements(IObjectModel)
    DIR_TABLE = "library_dir"
    LIB_TABLE = "library"
    INFO_TABLE = "media_info"
    MEDIA_OBJECT = None
    TYPE = ""

    def get_media_attributes(self):
        return self.MEDIA_OBJECT.attributes()

    def insert_dir(self, new_dir):
        return EditRecordQuery(self.DIR_TABLE) \
                .add_value("name", new_dir) \
                .add_value("type", 'directory') \
                .add_value("lib_type", self.TYPE) \
                .execute(commit=False)

    def insert_file(self, dir, filename, lastmodified):
        return EditRecordQuery(self.LIB_TABLE) \
                .add_value("directory", dir) \
                .add_value("name", filename) \
                .add_value("lastmodified", lastmodified) \
                .execute(commit=False)

    def update_file(self, id, lastmodified):
        return EditRecordQuery(self.LIB_TABLE) \
                .set_update_id("id", id) \
                .add_value("lastmodified", lastmodified) \
                .execute(commit=False)

    def remove_file(self, id):
        for (table, key) in [(self.LIB_TABLE, "id"), (self.INFO_TABLE, "id")]:
            DeleteQuery(table).append_where(key + " = %s", (id,)) \
                              .execute(commit=False)

    def remove_dir(self, id):
        f_ids = SimpleSelect(self.LIB_TABLE) \
                        .select_column("id") \
                        .append_where("directory = %s", id) \
                        .execute()
        self.remove_file(map(lambda i: i[0], f_ids))
        DeleteQuery(self.DIR_TABLE).append_where("id = %s", (id,)) \
                                   .execute(commit=False)

    def remove_recursive_dir(self, dir):
        files = self.get_all_files(dir)
        for file in files:
            self.remove_file(file[2])
        DeleteQuery(self.DIR_TABLE) \
                .append_where("name LIKE %s", (dir + u'%%',)) \
                .append_where("lib_type = %s", (self.TYPE,)) \
                .execute(commit=False)
        return [f[2] for f in files]

    def erase_empty_dir(self):
        dirlist = SimpleSelect(self.DIR_TABLE) \
                        .select_column("name") \
                        .append_where("lib_type = %s", self.TYPE) \
                        .execute()
        for (dirname,) in dirlist:
            rs = self.get_all_files(dirname)
            if len(rs) == 0:  # remove directory
                DeleteQuery(self.DIR_TABLE) \
                        .append_where("name = %s", (dirname,)) \
                        .execute(commit=False)

    def set_media_infos(self, file_id, infos, allow_create=True):
        rowcount = 0
        for k, v in infos.items():
            rowcount += ReplaceQuery(self.INFO_TABLE) \
                            .add_value("id", file_id) \
                            .add_value("ikey", k) \
                            .add_value("value", v) \
                            .execute(commit=False, expected_result="rowcount")
        return rowcount

    def is_file_exist(self, dirname, filename):
        return LibrarySelectQuery(self.DIR_TABLE) \
                .select_column("id", self.DIR_TABLE) \
                .select_column("id", self.LIB_TABLE) \
                .select_column("lastmodified", self.LIB_TABLE) \
                .append_where(self.DIR_TABLE + ".name = %s", dirname) \
                .append_where(self.LIB_TABLE + ".name = %s", filename) \
                .append_where("lib_type = %s", self.TYPE) \
                .execute(expected_result="fetchone")

    def is_dir_exist(self, dirname):
        rs = SimpleSelect(self.DIR_TABLE) \
                    .select_column("id") \
                    .append_where("name = %s", dirname) \
                    .append_where("lib_type = %s", self.TYPE) \
                    .execute(expected_result="fetchone")
        return rs and rs[0]

    def get_all_dirs(self, dir):
        return SimpleSelect(self.DIR_TABLE) \
                    .select_column("id", "name") \
                    .append_where("name LIKE %s", dir + u"%%") \
                    .append_where("type = 'directory'") \
                    .append_where("lib_type = %s", self.TYPE) \
                    .order_by("name") \
                    .execute()

    def get_all_files(self, dir):
        return LibrarySelectQuery(self.DIR_TABLE) \
                .select_column("id", self.DIR_TABLE) \
                .select_column("name", self.DIR_TABLE) \
                .select_column("id", self.LIB_TABLE) \
                .select_column("name", self.LIB_TABLE) \
                .select_column("lastmodified", self.LIB_TABLE) \
                .append_where(self.DIR_TABLE + ".name LIKE %s", dir + u"%%") \
                .append_where("lib_type = %s", self.TYPE) \
                .execute()

    def get_file_info(self, file_id, info_type):
        return SimpleSelect(self.INFO_TABLE).select_column("value") \
                    .append_where("id=%s AND ikey=%s", (file_id, info_type)) \
                    .execute(expected_result="fetchone")

    def get_file(self, dir, file):
        result = LibrarySelectQuery(self.DIR_TABLE) \
                .select_id() \
                .select_tags(self.MEDIA_OBJECT.attributes()) \
                .append_where(self.LIB_TABLE + ".name = %s", (file,)) \
                .append_where(self.DIR_TABLE + ".name = %s", (dir,)) \
                .append_where(self.DIR_TABLE + ".lib_type = %s", (self.TYPE,)) \
                .execute()
        return map(lambda m: self.MEDIA_OBJECT(m), result)

    def get_alldir_files(self, dir):
        result = LibrarySelectQuery(self.DIR_TABLE) \
                .select_id() \
                .select_tags(self.MEDIA_OBJECT.attributes()) \
                .append_where(self.DIR_TABLE + ".name LIKE %s", dir + u"%%") \
                .append_where(self.DIR_TABLE + ".lib_type = %s", (self.TYPE,)) \
                .execute()
        return map(lambda m: self.MEDIA_OBJECT(m), result)

    def get_dir_content(self, path):
        result = LibrarySelectQuery(self.DIR_TABLE) \
                .select_id() \
                .select_tags(self.MEDIA_OBJECT.attributes()) \
                .append_where(self.DIR_TABLE + ".name = %s", (path,)) \
                .append_where(self.DIR_TABLE + ".lib_type = %s", (self.TYPE,)) \
                .execute()
        return map(lambda m: self.MEDIA_OBJECT(m), result)

    def get_file_withids(self, file_ids):
        result = LibrarySelectQuery(self.DIR_TABLE) \
                .select_id() \
                .select_tags(self.MEDIA_OBJECT.attributes()) \
                .append_where(self.LIB_TABLE + ".id IN (%s)" % ",".join(map(str, file_ids))) \
                .append_where(self.DIR_TABLE + ".lib_type = %s", (self.TYPE,)) \
                .execute()
        return map(lambda m: self.MEDIA_OBJECT(m), result)

    def get_dircontent_id(self, dir):
        return LibrarySelectQuery(self.DIR_TABLE) \
                    .select_column("id") \
                    .append_where(self.DIR_TABLE + ".name = %s", (dir,)) \
                    .append_where(self.DIR_TABLE + ".lib_type = %s", (self.TYPE,)) \
                    .execute()

    def search_id(self, key, value):
        return SimpleSelect(self.INFO_TABLE) \
                .select_column("id") \
                .append_where("ikey=%s AND value=%s", (key, value)) \
                .execute()

    def list_tags(self, tag, filter):
        query = MediaSelectQuery()
        query.select_tag(tag)
        if filter is not None:
            filter.restrict(query)
        query.order_by_tag(tag)
        return query.execute()

    def search(self, filter, orders=[], limit=None):
        query = MediaSelectQuery()
        query.select_id()
        query.select_tags(self.MEDIA_OBJECT.attributes())
        filter.restrict(query)
        for (tag, direction) in orders:
            query.order_by_tag(tag, direction == "descending")
        query.set_limit(limit)
        return map(lambda m: self.MEDIA_OBJECT(m), query.execute())

    def get_dir_list(self, dir):
        cursor = DatabaseConnection().cursor()
        query = "SELECT d.id, d.name, COUNT(m.name) AS mediacount\
                 FROM library_dir d, library_dir sd, library m\
                 WHERE d.name LIKE %s AND\
                 SUBSTR(sd.name, 0, LENGTH(d.name)+1) = d.name AND\
                 sd.id=m.directory AND\
                 d.lib_type = %s AND\
                 sd.lib_type = %s\
                 GROUP BY d.id ORDER BY d.name"
        cursor.execute(query, (dir + unicode("/%%"), self.TYPE, self.TYPE))
        rs = cursor.fetchall()
        cursor.close()
        return rs

    def get_media_keys(self, type):
        cursor = DatabaseConnection().cursor()
        query = "SELECT DISTINCT m.ikey FROM media_info m\
                JOIN media_info m2 ON m.id = m2.id\
                WHERE m2.ikey='type' AND m2.value=%s"
        cursor.execute(query, (type,))
        rs = cursor.fetchall()
        cursor.close()
        return rs

class AudioLibrary(_Library):
    MEDIA_OBJECT = AudioItem
    TYPE = "audio"
    COVER_TABLE = "cover"

    def set_variousartist_tag(self, fid, file_info):
        cursor = DatabaseConnection().cursor()
        query = "SELECT DISTINCT m.id,m.value,m3.value FROM media_info m\
                JOIN media_info m2 ON m.id = m2.id\
                JOIN media_info m3 ON m.id = m3.id\
                WHERE m.ikey='various_artist' AND m2.ikey='album'\
                AND m2.value=%s AND m3.ikey='artist'"
        cursor.execute(query, (file_info["album"],))
        try: (id, various_artist, artist) = cursor.fetchone()
        except TypeError:  # first song of this album
            cursor.close()
            return
        else:
            need_update = False
            if various_artist == "__various__":
                need_update, ids = True, [(fid,)]
            elif artist != file_info["artist"]:
                need_update = True
                cursor.execute("SELECT id FROM media_info\
                        WHERE ikey='album' AND value=%s", (file_info["album"],))
                ids = cursor.fetchall()

        if need_update:
            cursor.executemany("UPDATE media_info SET value = '__various__'\
                    WHERE ikey='various_artist' AND id = %s", ids)
        cursor.close()

    def get_file_cover(self, file_id, source=False):
        var = source and "source" or "image"
        return ComplexSelect(self.COVER_TABLE) \
                    .join(self.INFO_TABLE, \
                        "%s.ikey = 'cover' AND %s.value = %s.id" \
                        % (self.INFO_TABLE, self.INFO_TABLE, self.COVER_TABLE)) \
                    .select_column("id") \
                    .select_column("mime_type") \
                    .select_column(var) \
                    .append_where(self.INFO_TABLE + ".id = %s", file_id) \
                    .execute(expected_result="fetchone")

    def is_cover_exist(self, source):
        return SimpleSelect(self.COVER_TABLE) \
                    .select_column("id", "lmod") \
                    .append_where("source=%s", source) \
                    .execute(expected_result="fetchone")

    def add_cover(self, source, mime, image):
        return EditRecordQuery(self.COVER_TABLE) \
                    .add_value("source", source) \
                    .add_value("mime_type", mime) \
                    .add_value("lmod", time.time()) \
                    .add_value("image", image) \
                    .execute(commit=False)

    def update_cover(self, id, mime, new_image):
        return EditRecordQuery(self.COVER_TABLE) \
                    .set_update_id("id", id) \
                    .add_value("mime_type", mime) \
                    .add_value("lmod", time.time()) \
                    .add_value("image", new_image) \
                    .execute(commit=False)

    def remove_cover(self, id):
        DeleteQuery(self.COVER_TABLE) \
                .append_where("id=%s", (id,)) \
                .execute(commit=False)

    def remove_unused_cover(self):
        s_query = SimpleSelect(self.INFO_TABLE) \
                    .select_column("value") \
                    .append_where("ikey = 'cover'")
        DeleteQuery(self.COVER_TABLE) \
                .append_where("id NOT IN (%s)" % s_query.to_sql(), ()) \
                .execute(commit=False)

class VideoLibrary(_Library):
    MEDIA_OBJECT = VideoItem
    TYPE = "video"


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