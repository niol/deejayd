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

import os, sys, time, base64
from deejayd.ui import log
from deejayd.database.querybuilders import *
from deejayd.model.mediafilters import MediaFilter
from deejayd import DeejaydError
from deejayd.model.media_item import AudioItem, VideoItem

class DatabaseQueries(object):

    def __init__(self, connection):
        self.connection = connection

    #
    # MediaDB requests
    #
    @query_decorator("lastid")
    def insert_file(self, cursor, dir, filename, lastmodified):
        query = "INSERT INTO library \
                (directory,name,lastmodified)VALUES(%s, %s, %s)"
        cursor.execute(query, (dir, filename, lastmodified))

    @query_decorator("none")
    def update_file(self, cursor, id, lastmodified):
        query = "UPDATE library SET lastmodified = %s WHERE id = %s"
        cursor.execute(query, (lastmodified, id))

    @query_decorator("rowcount")
    def set_media_infos(self, cursor, file_id, infos, allow_create=True):
        if allow_create:
            query = "REPLACE INTO media_info (id,ikey,value)VALUES(%s,%s,%s)"
            entries = [(file_id, k, v) for k, v in infos.items()]
        else:
            query = "UPDATE media_info SET value=%s WHERE id=%s and ikey=%s"
            entries = [(v, file_id, k) for k, v in infos.items()]
        cursor.executemany(query, entries)

    @query_decorator("none")
    def remove_file(self, cursor, id):
        queries = [
            "DELETE FROM library WHERE id = %s",
            "DELETE FROM media_info WHERE id = %s",
            "DELETE FROM medialist_libraryitem WHERE libraryitem_id = %s",
            ]
        for q in queries: cursor.execute(q, (id,))

    @query_decorator("fetchone")
    def is_file_exist(self, cursor, dirname, filename, type="audio"):
        query = "SELECT d.id, l.id, l.lastmodified \
            FROM library l JOIN library_dir d ON d.id=l.directory\
            WHERE l.name = %s AND d.name = %s AND d.lib_type = %s"
        cursor.execute(query, (filename, dirname, type))

    @query_decorator("lastid")
    def insert_dir(self, cursor, new_dir, type="audio"):
        query = "INSERT INTO library_dir (name,type,lib_type)VALUES(%s,%s,%s)"
        cursor.execute(query, (new_dir, 'directory', type))

    @query_decorator("none")
    def remove_dir(self, cursor, id):
        cursor.execute("SELECT id FROM library WHERE directory = %s", (id,))
        for (id,) in cursor.fetchall():
            self.remove_file(id)
        cursor.execute("DELETE FROM library_dir WHERE id = %s", (id,))

    @query_decorator("none")
    def remove_recursive_dir(self, cursor, dir, type="audio"):
        files = self.get_all_files(dir, type)
        for file in files: self.remove_file(file[2])
        cursor.execute("DELETE FROM library_dir\
                      WHERE name LIKE %s AND lib_type = %s", (dir + u"%%", type))
        return [f[2] for f in files]

    @query_decorator("custom")
    def is_dir_exist(self, cursor, dirname, type):
        cursor.execute("SELECT id FROM library_dir\
            WHERE name=%s AND lib_type=%s", (dirname, type))
        rs = cursor.fetchone()
        return rs and rs[0]

    @query_decorator("fetchall")
    def get_dir_list(self, cursor, dir, t="audio"):
        query = "SELECT d.id, d.name, COUNT(m.name) AS mediacount\
                 FROM library_dir d, library_dir sd, library m\
                 WHERE d.name LIKE %s AND\
                 SUBSTR(sd.name, 0, LENGTH(d.name)+1) = d.name AND\
                 sd.id=m.directory AND\
                 d.lib_type = %s AND\
                 sd.lib_type = %s\
                 GROUP BY d.id ORDER BY d.name"
        cursor.execute(query, (dir + unicode("/%%"), t, t))

    @query_decorator("fetchone")
    def get_file_info(self, cursor, file_id, info_type):
        query = "SELECT value FROM media_info WHERE id = %s AND ikey = %s"
        cursor.execute(query, (file_id, info_type))

    @query_decorator("fetchall")
    def get_all_files(self, cursor, dir, type="audio"):
        query = "SELECT DISTINCT d.id, d.name, l.id, l.name, l.lastmodified\
            FROM library l JOIN library_dir d ON d.id=l.directory\
            WHERE d.name LIKE %s AND d.lib_type = %s ORDER BY d.name,l.name"
        cursor.execute(query, (dir + u"%%", type))

    @query_decorator("fetchall")
    def get_all_dirs(self, cursor, dir, type="audio"):
        query = "SELECT DISTINCT id,name FROM library_dir\
            WHERE name LIKE %s AND type='directory' AND lib_type = %s\
            ORDER BY name"
        cursor.execute(query, (dir + u"%%", type))

    def _medialist_answer(self, answer, infos=[]):
        cls = {
            "song": AudioItem,
            "video": VideoItem,
        }
        files = []
        for m in answer:
            current = cls[m[3]](m, m[0])
            files.append(current)

        return files

    def _build_media_query(self, infos_list):
        selectquery = "i.id"
        joinquery = ""
        for index, key in enumerate(infos_list):
            selectquery += ",i%d.value" % index
            joinquery += " LEFT OUTER JOIN media_info i%d ON i%d.id=i.id AND\
                i%d.ikey='%s'" % (index, index, index, key)
        return selectquery, joinquery

    @query_decorator("medialist")
    def get_dir_content(self, cursor, dir, infos=[], type="audio"):
        selectquery, joinquery = self._build_media_query(infos)
        query = "SELECT DISTINCT " + selectquery + \
            " FROM library l JOIN library_dir d ON d.id=l.directory\
                           LEFT OUTER JOIN media_info i ON i.id=l.id"\
                           + joinquery + \
            " WHERE d.name = %s AND d.lib_type = %s ORDER BY d.name,l.name"
        cursor.execute(query, (dir, type))

    @query_decorator("medialist")
    def get_file(self, cursor, dir, file, infos=[], type="audio"):
        selectquery, joinquery = self._build_media_query(infos)
        query = "SELECT DISTINCT " + selectquery + \
            " FROM library l JOIN library_dir d ON d.id=l.directory\
                           JOIN media_info i ON i.id=l.id"\
                           + joinquery + \
            " WHERE d.name = %s AND l.name = %s AND d.lib_type = %s"
        cursor.execute(query, (dir, file, type))

    @query_decorator("medialist")
    def get_file_withids(self, cursor, file_ids, infos=[], type="audio"):
        selectquery, joinquery = self._build_media_query(infos)
        query = "SELECT DISTINCT " + selectquery + \
            " FROM library l JOIN library_dir d ON d.id=l.directory\
                           JOIN media_info i ON i.id=l.id"\
                           + joinquery + \
            " WHERE l.id IN (%s) AND d.lib_type = '%s'" % \
                (",".join(map(str, file_ids)), type)
        cursor.execute(query)

    @query_decorator("medialist")
    def get_alldir_files(self, cursor, dir, infos=[], type="audio"):
        selectquery, joinquery = self._build_media_query(infos)
        query = "SELECT DISTINCT " + selectquery + \
            " FROM library l JOIN library_dir d ON d.id=l.directory\
                           JOIN media_info i ON i.id=l.id"\
                           + joinquery + \
            " WHERE d.name LIKE %s AND d.lib_type = %s ORDER BY d.name,l.name"
        cursor.execute(query, (dir + u"%%", type))

    @query_decorator("fetchall")
    def get_dircontent_id(self, cursor, dir, type):
        query = "SELECT l.id\
            FROM library l JOIN library_dir d ON l.directory = d.id\
            WHERE d.lib_type = %s AND d.name = %s"
        cursor.execute(query, (type, dir))

    @query_decorator("fetchall")
    def search_id(self, cursor, key, value):
        query = "SELECT DISTINCT id FROM media_info WHERE ikey=%s AND value=%s"
        cursor.execute(query, (key, value))

    @query_decorator("medialist")
    def search(self, cursor, filter, infos=[], orders=[], limit=None):
        query = MediaSelectQuery()
        query.select_id()
        for tag in infos:
            query.select_tag(tag)
        filter.restrict(query)
        for (tag, direction) in orders:
            query.order_by_tag(tag, direction == "descending")
        query.set_limit(limit)
        cursor.execute(query.to_sql(), query.get_args())

    @query_decorator("fetchall")
    def list_tags(self, cursor, tag, filter):
        query = MediaSelectQuery()
        query.select_tag(tag)
        if filter is not None:
            filter.restrict(query)
        query.order_by_tag(tag)
        cursor.execute(query.to_sql(), query.get_args())

    @query_decorator("fetchall")
    def get_media_keys(self, cursor, type):
        query = "SELECT DISTINCT m.ikey FROM media_info m\
                JOIN media_info m2 ON m.id = m2.id\
                WHERE m2.ikey='type' AND m2.value=%s"
        cursor.execute(query, (type,))
#
# Post update action
#
    @query_decorator("none")
    def set_variousartist_tag(self, cursor, fid, file_info):
        query = "SELECT DISTINCT m.id,m.value,m3.value FROM media_info m\
                JOIN media_info m2 ON m.id = m2.id\
                JOIN media_info m3 ON m.id = m3.id\
                WHERE m.ikey='various_artist' AND m2.ikey='album'\
                AND m2.value=%s AND m3.ikey='artist'"
        cursor.execute(query, (file_info["album"],))
        try: (id, various_artist, artist) = cursor.fetchone()
        except TypeError:  # first song of this album
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

    @query_decorator("none")
    def erase_empty_dir(self, cursor, type="audio"):
        cursor.execute("SELECT DISTINCT name FROM library_dir\
            WHERE lib_type=%s", (type,))
        for (dirname,) in cursor.fetchall():
            rs = self.get_all_files(dirname, type)
            if len(rs) == 0:  # remove directory
                cursor.execute("DELETE FROM library_dir WHERE name = %s", \
                    (dirname,))

    @query_decorator("none")
    def update_stats(self, cursor, type="audio"):
        # record mediadb stats
        query = "UPDATE stats SET value = \
          (SELECT COUNT(DISTINCT m.value) FROM media_info m JOIN media_info m2\
            ON m.id = m2.id WHERE m.ikey=%s AND m2.ikey='type' AND m2.value=%s)\
          WHERE name = %s"
        if type == "audio":
            values = [("uri", "song", "songs"),
                    ("artist", "song", "artists"),
                    ("genre", "song", "genres"),
                    ("album", "song", "albums")]
        elif type == "video":
            values = [("uri", "video", "videos")]
        cursor.executemany(query, values)

        # update last updated stats
        cursor.execute("UPDATE stats SET value = %s WHERE name = %s", \
            (time.time(), type + "_library_update"))

    #
    # cover requests
    #
    @query_decorator("fetchone")
    def get_file_cover(self, cursor, file_id, source=False):
        var = source and "source" or "image"
        query = "SELECT c.id, c.mime_type, c." + var + \
            " FROM media_info m JOIN cover c\
                              ON m.ikey = 'cover' AND m.value = c.id\
            WHERE m.id = %s"
        cursor.execute(query, (file_id,))

    @query_decorator("fetchone")
    def is_cover_exist(self, cursor, source):
        query = "SELECT id,lmod FROM cover WHERE source=%s"
        cursor.execute(query, (source,))

    @query_decorator("lastid")
    def add_cover(self, cursor, source, mime, image):
        query = "INSERT INTO cover (source,mime_type,lmod,image)\
                VALUES(%s,%s,%s,%s)"
        cursor.execute(query, (source, mime, time.time(), image))

    @query_decorator("none")
    def update_cover(self, cursor, id, mime, new_image):
        query = "UPDATE cover SET mime_type = %s, lmod = %s, image = %s\
                WHERE id=%s"
        cursor.execute(query, (mime, time.time(), new_image, id))

    @query_decorator("none")
    def remove_cover(self, cursor, id):
        query = "DELETE FROM cover WHERE id=%s"
        cursor.execute(query, (id,))

    @query_decorator("none")
    def remove_unused_cover(self, cursor):
        query = "DELETE FROM cover WHERE id NOT IN \
                  (SELECT DISTINCT value FROM media_info WHERE ikey = 'cover')"
        cursor.execute(query)

    #
    # Stat requests
    #
    @query_decorator("fetchall")
    def get_stats(self, cursor):
        cursor.execute("SELECT * FROM stats")

    def close(self):
        self.connection.close()

# vim: ts=4 sw=4 expandtab