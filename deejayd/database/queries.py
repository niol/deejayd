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
from deejayd.mediafilters import *
from deejayd.ui import log
from deejayd.database.querybuilders import *
from deejayd.database.dbobjects import SQLizer


############################################################################
class MediaFile(dict):

    def __init__(self, db, file_id):
        self.db = db
        self["media_id"] = file_id

    def set_info(self, key, value):
        self.set_infos({key: value})

    def set_infos(self, infos):
        self.db.set_media_infos(self["media_id"], infos)
        self.db.connection.commit()
        self.update(infos)

    def played(self):
        played = int(self["playcount"]) + 1
        timestamp = int(time.time())
        self.set_infos({"playcount":str(played), "lastplayed":str(timestamp)})

    def skip(self):
        skip = int(self["skipcount"]) + 1
        self.set_info("skipcount", str(skip))

    def get_cover(self):
        if self["type"] != "song":
            raise AttributeError
        try: (id, mime, cover) = self.db.get_file_cover(self["media_id"])
        except TypeError:
            raise AttributeError
        return {"cover": base64.b64decode(cover), "id":id, "mime": mime}

    def replay_gain(self):
        """Return the recommended Replay Gain scale factor."""
        try:
            db = float(self["replaygain_track_gain"].split()[0])
            peak = self["replaygain_track_peak"] and\
                     float(self["replaygain_track_peak"]) or 1.0
        except (KeyError, ValueError, IndexError):
            return 1.0
        else:
            scale = 10.**(db / 20)
            if scale * peak > 1:
                scale = 1.0 / peak # don't clip
            return min(15, scale)

############################################################################


class DatabaseQueries(object):
    structure_created = False

    def __init__(self, connection):
        self.connection = connection
        self.sqlizer = SQLizer()

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
    def set_media_infos(self, cursor, file_id, infos, allow_create = True):
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
    def is_file_exist(self, cursor, dirname, filename, type = "audio"):
        query = "SELECT d.id, l.id \
            FROM library l JOIN library_dir d ON d.id=l.directory\
            WHERE l.name = %s AND d.name = %s AND d.lib_type = %s"
        cursor.execute(query,(filename, dirname, type))

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
                      WHERE name LIKE %s AND lib_type = %s", (dir+u"%%", type))
        return [f[2] for f in files]

    @query_decorator("custom")
    def is_dir_exist(self, cursor, dirname, type):
        cursor.execute("SELECT id FROM library_dir\
            WHERE name=%s AND lib_type=%s", (dirname, type))
        rs = cursor.fetchone()
        return rs and rs[0]

    @query_decorator("none")
    def insert_dirlink(self, cursor, new_dirlink, type="audio"):
        query = "INSERT INTO library_dir (name,type,lib_type)VALUES(%s,%s,%s)"
        cursor.execute(query, (new_dirlink, "dirlink", type))

    @query_decorator("none")
    def remove_dirlink(self, cursor, dirlink, type="audio"):
        query = "DELETE FROM library_dir\
                 WHERE name = %s AND\
                       type = 'dirlink' AND\
                       lib_type = %s"
        cursor.execute(query, (dirlink, type))

    @query_decorator("fetchall")
    def get_dir_list(self, cursor, dir, t = "audio"):
        query = "SELECT DISTINCT id, name FROM library_dir\
                 WHERE name LIKE %s AND\
                       lib_type = %s AND\
                       type = 'directory'\
                 ORDER BY name"
        term = dir == unicode("") and u"%%" or dir+unicode("/%%")
        cursor.execute(query, (term, t))

    @query_decorator("fetchone")
    def get_file_info(self, cursor, file_id, info_type):
        query = "SELECT value FROM media_info WHERE id = %s AND ikey = %s"
        cursor.execute(query, (file_id, info_type))

    @query_decorator("fetchall")
    def get_all_files(self, cursor, dir, type = "audio"):
        query = "SELECT DISTINCT d.id, d.name, l.id, l.name, l.lastmodified\
            FROM library l JOIN library_dir d ON d.id=l.directory\
            WHERE d.name LIKE %s AND d.lib_type = %s ORDER BY d.name,l.name"
        cursor.execute(query,(dir+u"%%", type))

    @query_decorator("fetchall")
    def get_all_dirs(self, cursor, dir, type = "audio"):
        query = "SELECT DISTINCT id,name FROM library_dir\
            WHERE name LIKE %s AND type='directory' AND lib_type = %s\
            ORDER BY name"
        cursor.execute(query,(dir+u"%%", type))

    @query_decorator("fetchall")
    def get_all_dirlinks(self, cursor, dir, type = 'audio'):
        if not dir[:-1] == '/': dir = dir+ u'/'

        query = "SELECT DISTINCT id,name FROM library_dir\
            WHERE name LIKE %s AND type='dirlink' AND lib_type = %s\
            ORDER BY name"
        cursor.execute(query,(dir+u"%%", type))

    def _medialist_answer(self, answer, infos = []):
        files = []
        for m in answer:
            current = MediaFile(self, m[0])
            for index, attr in enumerate(infos):
                current[attr] = m[index+1]
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
    def get_dir_content(self, cursor, dir, infos = [], type = "audio"):
        selectquery, joinquery = self._build_media_query(infos)
        query = "SELECT DISTINCT "+ selectquery +\
            " FROM library l JOIN library_dir d ON d.id=l.directory\
                           LEFT OUTER JOIN media_info i ON i.id=l.id"\
                           + joinquery+\
            " WHERE d.name = %s AND d.lib_type = %s ORDER BY d.name,l.name"
        cursor.execute(query,(dir, type))

    @query_decorator("medialist")
    def get_file(self, cursor, dir, file, infos = [], type = "audio"):
        selectquery, joinquery = self._build_media_query(infos)
        query = "SELECT DISTINCT "+ selectquery +\
            " FROM library l JOIN library_dir d ON d.id=l.directory\
                           JOIN media_info i ON i.id=l.id"\
                           + joinquery+\
            " WHERE d.name = %s AND l.name = %s AND d.lib_type = %s"
        cursor.execute(query, (dir, file, type))

    @query_decorator("medialist")
    def get_file_withids(self, cursor, file_ids, infos=[], type="audio"):
        selectquery, joinquery = self._build_media_query(infos)
        query = "SELECT DISTINCT "+ selectquery +\
            " FROM library l JOIN library_dir d ON d.id=l.directory\
                           JOIN media_info i ON i.id=l.id"\
                           + joinquery+\
            " WHERE l.id IN (%s) AND d.lib_type = '%s'" % \
                (",".join(map(str,file_ids)), type)
        cursor.execute(query)

    @query_decorator("medialist")
    def get_alldir_files(self, cursor, dir, infos = [], type = "audio"):
        selectquery, joinquery = self._build_media_query(infos)
        query = "SELECT DISTINCT "+ selectquery +\
            " FROM library l JOIN library_dir d ON d.id=l.directory\
                           JOIN media_info i ON i.id=l.id"\
                           + joinquery+\
            " WHERE d.name LIKE %s AND d.lib_type = %s ORDER BY d.name,l.name"
        cursor.execute(query,(dir+u"%%", type))

    @query_decorator("fetchall")
    def get_dircontent_id(self, cursor, dir, type):
        query = "SELECT l.id\
            FROM library l JOIN library_dir d ON l.directory = d.id\
            WHERE d.lib_type = %s AND d.name = %s"
        cursor.execute(query,(type, dir))

    @query_decorator("fetchall")
    def search_id(self, cursor, key, value):
        query = "SELECT DISTINCT id FROM media_info WHERE ikey=%s AND value=%s"
        cursor.execute(query,(key, value))

    @query_decorator("medialist")
    def search(self, cursor, filter, infos = [], orders = [], limit = None):
        filter = self.sqlizer.translate(filter)
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
        filter = self.sqlizer.translate(filter)
        query = MediaSelectQuery()
        query.select_tag(tag)
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
        except TypeError: # first song of this album
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
    def erase_empty_dir(self, cursor, type = "audio"):
        cursor.execute("SELECT DISTINCT name FROM library_dir\
            WHERE lib_type=%s", (type,))
        for (dirname,) in cursor.fetchall():
            rs = self.get_all_files(dirname, type)
            if len(rs) == 0: # remove directory
                cursor.execute("DELETE FROM library_dir WHERE name = %s",\
                    (dirname,))

    @query_decorator("none")
    def update_stats(self, cursor, type = "audio"):
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
        cursor.execute("UPDATE stats SET value = %s WHERE name = %s",\
            (time.time(),type+"_library_update"))

    #
    # cover requests
    #
    @query_decorator("fetchone")
    def get_file_cover(self, cursor, file_id, source = False):
        var = source and "source" or "image"
        query = "SELECT c.id, c.mime_type, c." + var +\
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
    # common medialist requests
    #
    @query_decorator("fetchall")
    def get_medialist_list(self, cursor):
        query = SimpleSelect('medialist')
        query.select_column('id', 'name', 'type')
        query.order_by('name')
        cursor.execute(query.to_sql(), query.get_args())

    @query_decorator("custom")
    def get_medialist_id(self, cursor, pl_name, pl_type = 'static'):
        query = SimpleSelect('medialist')
        query.select_column('id')
        query.append_where("name = %s", (pl_name, ))
        query.append_where("type = %s", (pl_type, ))
        cursor.execute(query.to_sql(), query.get_args())

        ans = cursor.fetchone()
        if ans is None: raise ValueError
        return ans[0]

    @query_decorator("fetchone")
    def is_medialist_exists(self, cursor, pl_id):
        query = SimpleSelect('medialist')
        query.select_column('id', 'name', 'type')
        query.append_where("id = %s", (pl_id, ))
        cursor.execute(query.to_sql(), query.get_args())

    @query_decorator("none")
    def delete_medialist(self, cursor, ml_id):
        try: ml_id, name, type = self.is_medialist_exists(ml_id)
        except TypeError:
            return
        if type == "static":
            query = "DELETE FROM medialist_libraryitem WHERE medialist_id = %s"
            cursor.execute(query, (ml_id,))
        elif type == "magic":
            for (filter_id,) in self.__get_medialist_filterids(cursor, ml_id):
                self.delete_filter(cursor, filter_id)
            cursor.execute(\
              "DELETE FROM medialist_filters WHERE medialist_id=%s", (ml_id,))
            # delete medialist properties
            cursor.execute(\
              "DELETE FROM medialist_property WHERE medialist_id=%s", (ml_id,))
            # delete medialist sort
            cursor.execute(\
              "DELETE FROM medialist_sorts WHERE medialist_id=%s", (ml_id,))
        cursor.execute("DELETE FROM medialist WHERE id = %s", (ml_id,))
        self.connection.commit()

    def get_filter(self, cursor, id):
        try: filter_type = self.__get_filter_type(cursor, id)
        except ValueError:
            return None
        if filter_type == 'basic':
            return self.__get_basic_filter(cursor, id)
        elif filter_type == 'complex':
            return self.__get_complex_filter(cursor, id)

    def delete_filter(self, cursor, filter_id):
        try: filter_type = self.__get_filter_type(cursor, filter_id)
        except ValueError:
            return None

        if filter_type == 'basic':
            cursor.execute("DELETE FROM filters_basicfilters\
                WHERE filter_id = %s", (filter_id,))
        elif filter_type == 'complex':
            # get filters id associated with this filter
            query = SimpleSelect('filters_complexfilters_subfilters')
            query.select_column('filter_id')
            query.append_where("complexfilter_id = %s", (filter_id, ))
            cursor.execute(query.to_sql(), query.get_args())

            for (id,) in cursor.fetchall():
                self.delete_filter(cursor, id)
                cursor.execute("DELETE FROM filters_complexfilters_subfilters \
                    WHERE complexfilter_id = %s AND filter_id = %s",\
                    (filter_id, id))
            cursor.execute("DELETE FROM filters_complexfilters \
                WHERE filter_id = %s",(filter_id,))

        cursor.execute("DELETE FROM filters WHERE filter_id = %s",(filter_id,))

    def __get_filter_type(self, cursor, filter_id):
        query = SimpleSelect('filters')
        query.select_column('type')
        query.append_where("filter_id = %s", (filter_id, ))
        cursor.execute(query.to_sql(), query.get_args())
        record = cursor.fetchone()

        if not record: raise ValueError
        return record[0]

    def __get_basic_filter(self, cursor, id):
        query = SimpleSelect('filters_basicfilters')
        query.select_column('tag', 'operator', 'pattern')
        query.append_where("filter_id = %s", (id, ))
        cursor.execute(query.to_sql(), query.get_args())
        record = cursor.fetchone()

        if record:
            bfilter_class = NAME2BASIC[record[1]]
            f = bfilter_class(record[0], record[2])
            return f

    def __get_complex_filter(self, cursor, id):
        query = SimpleSelect('filters_complexfilters')
        query.select_column('combinator')
        query.append_where("filter_id = %s", (id, ))
        cursor.execute(query.to_sql(), query.get_args())
        record = cursor.fetchone()

        if record:
            cfilter_class = NAME2COMPLEX[record[0]]
            query = SimpleSelect('filters_complexfilters_subfilters')
            query.select_column('filter_id')
            query.append_where("complexfilter_id = %s", (id, ))
            cursor.execute(query.to_sql(), query.get_args())
            sf_records = cursor.fetchall()
            filterlist = []
            for sf_record in sf_records:
                sf_id = sf_record[0]
                filterlist.append(self.get_filter(cursor, sf_id))
            cfilter = cfilter_class(*filterlist)
            return cfilter

    def __get_medialist_filterids(self, cursor, ml_id):
        query = SimpleSelect('medialist_filters')
        query.select_column('filter_id')
        query.append_where("medialist_id = %s", (ml_id, ))
        cursor.execute(query.to_sql(), query.get_args())

        return cursor.fetchall()

    def __add_medialist_filters(self, cursor, pl_id, filters):
        filter_ids = []
        for filter in filters:
            filter_id = self.sqlizer.translate(filter).save(self)
            if filter_id: filter_ids.append((pl_id, filter_id))
        cursor.executemany("INSERT INTO medialist_filters\
            (medialist_id,filter_id)VALUES(%s,%s)", filter_ids)

    @query_decorator("custom")
    def get_magic_medialist_filters(self, cursor, ml_id):
        rs = self.__get_medialist_filterids(cursor, ml_id)
        if not rs: return []
        filters = []
        for (filter_id,) in rs:
            filter = self.get_filter(cursor, filter_id)
            if filter: filters.append(filter)
        return filters

    @query_decorator("custom")
    def set_magic_medialist_filters(self, cursor, pl_name, filters):
        slt_query = "SELECT id FROM medialist WHERE name=%s AND type = 'magic'"
        cursor.execute(slt_query, (pl_name,))
        rs = cursor.fetchone()
        if not rs:
            query = "INSERT INTO medialist (name,type)VALUES(%s,'magic')"
            cursor.execute(query, (pl_name,))
            id = self.connection.get_last_insert_id(cursor)
        else: (id,) = rs

        for (filter_id,) in self.__get_medialist_filterids(cursor, id):
            self.delete_filter(cursor, filter_id)
        cursor.execute(\
          "DELETE FROM medialist_filters WHERE medialist_id=%s", (id,))

        self.__add_medialist_filters(cursor, id, filters)
        self.connection.commit()
        return id

    @query_decorator("none")
    def add_magic_medialist_filters(self, cursor, pl_id, filters):
        self.__add_medialist_filters(cursor, pl_id, filters)
        self.connection.commit()

    @query_decorator("fetchall")
    def get_magic_medialist_sorts(self, cursor, ml_id):
        query = "SELECT tag,direction FROM medialist_sorts\
                WHERE medialist_id = %s"
        cursor.execute(query, (ml_id,))

    @query_decorator("none")
    def set_magic_medialist_sorts(self, cursor, ml_id, sorts):
        # first, delete all previous sort for this medialist
        cursor.execute("DELETE FROM medialist_sorts WHERE medialist_id=%s",\
                (ml_id,))
        cursor.executemany("INSERT INTO medialist_sorts\
            (medialist_id,tag,direction)VALUES(%s,%s,%s)",\
            [ (ml_id, tag, direction) for (tag, direction) in sorts])
        self.connection.commit()

    @query_decorator("fetchall")
    def get_magic_medialist_properties(self, cursor, ml_id):
        query = "SELECT ikey,value FROM medialist_property\
                WHERE medialist_id = %s"
        cursor.execute(query, (ml_id,))

    @query_decorator("none")
    def set_magic_medialist_property(self, cursor, ml_id, key, value):
        cursor.execute("REPLACE INTO medialist_property\
            (medialist_id,ikey,value)VALUES(%s,%s,%s)", (ml_id, key, value))
        self.connection.commit()

######################################
###### Static medialist queries ######
######################################
    @query_decorator("none")
    def add_to_static_medialist(self, cursor, ml_id, media_ids):
        query = "INSERT INTO medialist_libraryitem\
            (medialist_id, libraryitem_id) VALUES(%s,%s)"
        cursor.executemany(query, [(ml_id, mid) for mid in media_ids])

    @query_decorator("none")
    def clear_static_medialist(self, cursor, ml_id):
        query = "DELETE FROM medialist_libraryitem WHERE medialist_id = %s"
        cursor.execute(query, (ml_id,))
        self.connection.commit()

    @query_decorator("medialist")
    def get_static_medialist(self, cursor, ml_id, infos = []):
        selectquery, joinquery = self._build_media_query(infos)
        query = "SELECT DISTINCT "+ selectquery + ", mi.position " +\
            " FROM medialist m JOIN medialist_libraryitem mi\
                                    ON m.id = mi.medialist_id\
                           JOIN media_info i ON i.id=mi.libraryitem_id"\
                           + joinquery+\
            " WHERE m.id = %s AND m.type = 'static' ORDER BY mi.position"
        cursor.execute(query,(ml_id,))

    @query_decorator("custom")
    def set_static_medialist(self, cursor, name, content):
        slt_query = "SELECT id FROM medialist WHERE name=%s AND type = 'static'"
        cursor.execute(slt_query, (name,))
        rs = cursor.fetchone()
        if not rs:
            query = "INSERT INTO medialist (name,type)VALUES(%s,'static')"
            cursor.execute(query, (name,))
            id = self.connection.get_last_insert_id(cursor)
        else: (id,) = rs

        cursor.execute(\
            "DELETE FROM medialist_libraryitem WHERE medialist_id = %s",(id,))
        values = [(id, s["media_id"]) for s in content]
        query = "INSERT INTO medialist_libraryitem(medialist_id,libraryitem_id)\
            VALUES(%s,%s)"
        cursor.executemany(query,values)
        self.connection.commit()
        # return id of the playlist
        return id

    #
    # Webradio requests
    #
    @query_decorator("none")
    def set_webradio_stats(self, cursor, source, key, value):
        query = "REPLACE INTO webradio_stats\
                (source_id,key,value)VALUES(%s,%s,%s)"
        cursor.execute(query, (source, key, value))

    @query_decorator("fetchone")
    def get_webradio_stats(self, cursor, source, key):
        query = "SELECT value FROM webradio_stats WHERE source_id=%s AND key=%s"
        cursor.execute(query, (source, key))

    @query_decorator("custom")
    def get_webradio_source(self, cursor, source):
        cursor.execute("SELECT id FROM webradio_source WHERE name = %s",\
                            (source,))
        result = cursor.fetchall()
        if len(result) == 1:
            return result[0][0]
        else:
            query = "INSERT INTO webradio_source(name) VALUES(%s)"
            cursor.execute(query, (source,))
            return self.connection.get_last_insert_id(cursor)

    @query_decorator("fetchall")
    def get_webradio_categories(self, cursor, source_id):
        query = "SELECT name, id FROM webradio_categories WHERE source_id = %s"
        cursor.execute(query, (source_id,))

    @query_decorator("lastid")
    def add_webradio_category(self, cursor, source_id, category):
        query = "INSERT INTO webradio_categories (name,source_id)VALUES(%s,%s)"
        cursor.execute(query, (category, source_id))

    @query_decorator("none")
    def remove_webradio_categories(self, cursor, source_id, cat_ids):
        query = "SELECT id FROM webradio\
                WHERE cat_id IN (%s) AND source_id = %s"
        cursor.execute(query, (",".join(map(str, cat_ids)), source_id))
        w_ids  = [id for (id,) in cursor.fetchall()]

        query = "DELETE FROM webradio_categories\
                WHERE id IN (%s) AND source_id = %s"
        cursor.execute(query, (",".join(map(str, cat_ids)), source_id))
        # remove all webradio attached to these categories
        self.remove_webradios(source_id, w_ids)


    @query_decorator("none")
    def clear_webradio_categories(self, cursor, source_id):
        query = "DELETE FROM webradio_categories WHERE source_id = %s"
        cursor.execute(query, (source_id,))

        # remove all webradios
        self.clear_webradios(source_id)

    @query_decorator("fetchall")
    def get_webradios(self, cursor, source, cat_id = None):
        query = "SELECT DISTINCT w.id, w.name, e.url\
            FROM webradio w INNER JOIN webradio_entries e \
                            ON w.id = e.webradio_id\
                            WHERE w.source_id = %s"
        args = [source]
        if cat_id is not None:
            query += " AND w.cat_id = %s"
            args.append(cat_id)
        query += " ORDER BY w.id, e.id"
        cursor.execute(query, args)

    @query_decorator("custom")
    def add_webradio(self, cursor, s_id, name, urls, category = None):
        cat_id = category or -1
        query = "INSERT INTO webradio(name, source_id, cat_id)VALUES(%s,%s,%s)"
        cursor.execute(query, (name, s_id, cat_id))
        wid = self.connection.get_last_insert_id(cursor)

        query = "INSERT INTO webradio_entries(url, webradio_id)VALUES(%s,%s)"
        cursor.executemany(query, [(url,wid) for url in urls])
        self.connection.commit()

        return wid

    @query_decorator("none")
    def add_webradio_urls(self, cursor, w_id, urls):
        query = "INSERT INTO webradio_entries(url, webradio_id)VALUES(%s,%s)"
        cursor.executemany(query, [(url, w_id) for url in urls])
        self.connection.commit()

    @query_decorator("none")
    def remove_webradios(self, cursor, source_id, wids):
        query = "DELETE FROM webradio_entries WHERE webradio_id IN \
            (SELECT id FROM webradio WHERE source_id=%s AND id IN (%s))"
        cursor.execute(query, (source_id, ",".join(map(str, wids))))

        query = "DELETE FROM webradio WHERE source_id=%s AND id IN (%s)"
        cursor.execute(query, (source_id, ",".join(map(str, wids))))

        self.connection.commit()

    @query_decorator("none")
    def remove_url_from_webradio(self, cursor, wid, url_id):
        cursor.execute("DELETE FROM webradio_entries\
            WHERE webradio_id = %s AND id = %s", (wid, url_id))
        self.connection.commit()

    @query_decorator("none")
    def add_url_for_webradio(self, cursor, wid, url):
        cursor.execute("INSERT INTO webradio_entries (url, webradio_id)\
            VALUES(%s,%s)", (url, wid))
        self.connection.commit()

    @query_decorator("none")
    def clear_webradios(self, cursor, source_id):
        cursor.execute("DELETE FROM webradio_entries WHERE webradio_id IN \
            (SELECT id FROM webradio WHERE source_id=%s)", (source_id,))
        cursor.execute("DELETE FROM webradio WHERE source_id=%s", (source_id,))
        self.connection.commit()

    #
    # Stat requests
    #
    @query_decorator("fetchall")
    def get_stats(self, cursor):
        cursor.execute("SELECT * FROM stats")

    #
    # State requests
    #
    @query_decorator("none")
    def set_state(self, cursor, values):
        cursor.executemany("REPLACE INTO variables (value,name)VALUES(%s,%s)",\
                           values)
        self.connection.commit()

    @query_decorator("custom")
    def get_state(self, cursor, type):
        cursor.execute("SELECT value FROM variables WHERE name = %s",(type,))
        try:
            (rs,) =  cursor.fetchone()
            return rs
        except (ValueError, TypeError):
            return None

    def close(self):
        self.connection.close()

# vim: ts=4 sw=4 expandtab
