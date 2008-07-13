# Deejayd, a media player daemon
# Copyright (C) 2007-2008 Mickael Royer <mickael.royer@gmail.com>
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

import os, sys, time
from deejayd.ui import log
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
        if self["type"] != "audio":
            raise AttributeError
        try: (id, cover) = self.db.get_file_cover()
        except TypeError:
            return None
        return cover

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


class MediaSelectQuery(object):

    def __init__(self):
        self.selects = []
        self.joins = []
        self.__joined_tags = []
        self.wheres = []
        self.orders = []
        self.id = False

    def select_id(self):
        self.id = True

    def select_tag(self, tagname):
        self.selects.append("%s.value" % tagname)
        self.join_on_tag(tagname)

    def order_by_tag(self, tagname):
        self.orders.append("%s.value" % tagname)
        self.join_on_tag(tagname)

    def join_on_tag(self, tagname):
        if tagname not in self.__joined_tags:
            self.__joined_tags.append(tagname)
            j_st = "JOIN media_info %(tag)s ON %(tag)s.id == library.id\
                                            AND %(tag)s.ikey == '%(tag)s'"\
                   % { 'tag' : tagname }
            self.joins.append(j_st)

    def __str__(self):
        orders = None
        if len(self.orders) >= 1:
            orders = 'ORDER BY ' + ', '.join(self.orders)

        return "SELECT DISTINCT %s %s FROM library %s WHERE %s %s"\
               % (self.id and 'library.id,' or '',
                  ', '.join(self.selects),
                  ' '.join(self.joins),
                  ' AND '.join(self.wheres) or 1,
                  orders or '')

    def to_sql(self):
        return str(self)


def query_decorator(answer_type):
    def query_decorator_instance(func):

        def query_func(self, *__args, **__kw):
            cursor = self.connection.cursor()
            rs = func(self, cursor, *__args, **__kw)
            if answer_type == "lastid":
                rs = self.connection.get_last_insert_id(cursor)
            elif answer_type == "rowcount":
                rs = cursor.rowcount
            elif answer_type == "fetchall":
                rs = cursor.fetchall()
            elif answer_type == "fetchone":
                rs = cursor.fetchone()
            elif answer_type == "medialist":
                rs = self._medialist_answer(cursor.fetchall(),__kw['infos'])

            cursor.close()
            return rs

        return query_func

    return query_decorator_instance


class DatabaseQueries(object):
    structure_created = False

    def __init__(self, connection):
        self.connection = connection
        self.sqlizer = SQLizer()

    #
    # MediaDB requests
    #
    @query_decorator("lastid")
    def insert_file(self, cursor, dir, filename):
        query = "INSERT INTO library (directory,name)VALUES(%s, %s)"
        cursor.execute(query, (dir, filename))

    @query_decorator("rowcount")
    def set_media_infos(self, cursor, file_id, infos):
        query = "REPLACE INTO media_info (id,ikey,value)VALUES(%s,%s,%s)"
        entries = [(file_id, k, v) for k, v in infos.items()]
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

    @query_decorator("none")
    def erase_empty_dir(self, cursor, type = "audio"):
        cursor.execute("SELECT DISTINCT name FROM library_dir\
            WHERE lib_type=%s", (type,))
        for (dirname,) in cursor.fetchall():
            rs = self.get_all_files(dirname, type)
            if len(rs) == 0: # remove directory
                cursor.execute("DELETE FROM library_dir WHERE name = %s",\
                    (dirname,))

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
                      WHERE name LIKE %s AND lib_type = %s", (dir+"%%", type))
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
        query = "DELETE FROM library_dir WHERE name = %s AND lib_type = %s"
        cursor.execute(query, (dirlink, type))

    @query_decorator("fetchall")
    def get_dir_list(self, cursor, dir, type = "audio"):
        query = "SELECT DISTINCT id, name FROM library_dir\
            WHERE name LIKE %s AND lib_type = %s ORDER BY name"
        term = dir == "" and "%%" or dir+"/%%"
        cursor.execute(query, (term, type))

    @query_decorator("fetchone")
    def get_file_info(self, cursor, file_id, info_type):
        query = "SELECT value FROM media_info WHERE id = %s AND ikey = %s"
        cursor.execute(query, (file_id, info_type))

    @query_decorator("fetchall")
    def get_all_files(self, cursor, dir, type = "audio"):
        query = "SELECT DISTINCT d.id, d.name, l.id, l.name\
            FROM library l JOIN library_dir d ON d.id=l.directory\
            WHERE d.name LIKE %s AND d.lib_type = %s ORDER BY d.name,l.name"
        cursor.execute(query,(dir+"%%", type))

    @query_decorator("fetchall")
    def get_all_dirs(self, cursor, dir, type = "audio"):
        query = "SELECT DISTINCT id,name FROM library_dir\
            WHERE name LIKE %s AND type='directory' AND lib_type = %s\
            ORDER BY name"
        cursor.execute(query,(dir+"%%", type))

    @query_decorator("fetchall")
    def get_all_dirlinks(self, cursor, dirlink, type = 'audio'):
        query = "SELECT DISTINCT id,name FROM library_dir\
            WHERE name LIKE %s AND type='dirlink' AND lib_type = %s\
            ORDER BY name"
        cursor.execute(query,(dirlink+"%%", type))

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
            joinquery += " JOIN media_info i%d ON i%d.id=i.id AND\
                i%d.ikey='%s'" % (index, index, index, key)
        return selectquery, joinquery

    @query_decorator("medialist")
    def get_dir_content(self, cursor, dir, infos = [], type = "audio"):
        selectquery, joinquery = self._build_media_query(infos)
        query = "SELECT DISTINCT "+ selectquery +\
            " FROM library l JOIN library_dir d ON d.id=l.directory\
                           JOIN media_info i ON i.id=l.id"\
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
        cursor.execute(query,(dir+"%%", type))

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
    def search(self, cursor, filter, infos = []):
        filter = self.sqlizer.translate(filter)
        query = MediaSelectQuery()
        query.select_id()
        for tag in infos:
            query.select_tag(tag)
        filter.restrict(query)
        cursor.execute(query.to_sql())

    @query_decorator("fetchall")
    def list_tags(self, cursor, tag, filter):
        filter = self.sqlizer.translate(filter)
        query = MediaSelectQuery()
        query.select_tag(tag)
        filter.restrict(query)
        query.order_by_tag(tag)
        cursor.execute(query.to_sql())

    #
    # cover requests
    #
    @query_decorator("fetchone")
    def get_file_cover(self, cursor, file_id):
        query = "SELECT c.id, c.image \
            FROM media_info m JOIN cover c\
                              ON m.ikey = 'cover' AND m.value = c.id\
            WHERE m.id = %s"
        cursor.execute(query, (file_id,))

    @query_decorator("fetchone")
    def is_cover_exist(self, cursor, source):
        query = "SELECT id,lmod FROM cover WHERE source=%s"
        cursor.execute(query, (source,))

    @query_decorator("lastid")
    def add_cover(self, cursor, source, image):
        query = "INSERT INTO cover (source,lmod,image)VALUES(%s,%s,%s)"
        cursor.execute(query, (source, time.time(), image))

    @query_decorator("none")
    def update_cover(self, cursor, id, new_image):
        query = "UPDATE cover SET lmod = %s, image = %s WHERE id=%s"
        cursor.execute(query, (time.time(), new_image, id))

    @query_decorator("none")
    def remove_cover(self, cursor, id):
        query = "DELETE FROM cover WHERE id=%s"
        cursor.execute(query, (id,))

    #
    # static medialist requests
    #
    @query_decorator("custom")
    def is_static_medialist_exists(self, cursor, name):
        query = "SELECT id FROM medialist m\
                    WHERE m.name = %s AND m.type = 'static'"
        cursor.execute(query,(name,))
        rs = cursor.fetchone()
        return rs and rs[0]

    @query_decorator("none")
    def add_to_static_medialist(self, cursor, pl_id, media_ids):
        query = "INSERT INTO medialist_libraryitem\
            ('medialist_id','libraryitem_id') VALUES(%s,%s)"
        cursor.executemany(query, [(pl_id, mid) for mid in media_ids])

    @query_decorator("medialist")
    def get_static_medialist(self, cursor, name, infos = []):
        selectquery, joinquery = self._build_media_query(infos)
        query = "SELECT DISTINCT "+ selectquery + ", mi.position " +\
            " FROM medialist m JOIN medialist_libraryitem mi\
                                    ON m.id = mi.medialist_id\
                           JOIN media_info i ON i.id=mi.libraryitem_id"\
                           + joinquery+\
            " WHERE m.name = %s AND m.type = 'static' ORDER BY mi.position"
        cursor.execute(query,(name,))

    @query_decorator("none")
    def delete_static_medialist(self, cursor, name):
        # get id of medialist entries
        query = "SELECT id FROM medialist WHERE name=%s AND type = 'static'"
        cursor.execute(query ,(name,))
        try: (id,) = cursor.fetchone()
        except (IndexError, TypeError): return # medialist does not exist
        # remove medialist entries
        cursor.execute("DELETE FROM medialist_libraryitem\
            WHERE medialist_id = %s",(id,))
        cursor.execute("DELETE FROM medialist WHERE id = %s",(id,))
        self.connection.commit()

    @query_decorator("none")
    def set_static_medialist(self, cursor, name, content):
        slt_query = "SELECT id FROM medialist WHERE name=%s AND type = 'static'"
        cursor.execute(slt_query, (name,))
        rs = cursor.fetchone()
        if not rs:
            query = "INSERT INTO medialist (name,type)VALUES(%s,'static')"
            cursor.execute(query, (name,))
            self.connection.commit()
            cursor.execute(slt_query,(name,))
            (id,) = cursor.fetchone()
        else: (id,) = rs

        cursor.execute(\
            "DELETE FROM medialist_libraryitem WHERE medialist_id = %s",(id,))
        values = [(id, s["media_id"]) for s in content]
        query = "INSERT INTO medialist_libraryitem(medialist_id,libraryitem_id)\
            VALUES(%s,%s)"
        cursor.executemany(query,values)
        self.connection.commit()

    @query_decorator("fetchall")
    def get_medialist_list(self, cursor, type = 'static'):
        query = "SELECT m.name, COUNT(mi.position)\
            FROM medialist m JOIN medialist_libraryitem mi\
                ON m.id = mi.medialist_id WHERE m.type = %s GROUP BY m.name"
        cursor.execute(query, (type,))

    #
    # Webradio requests
    #
    @query_decorator("fetchall")
    def get_webradios(self, cursor):
        cursor.execute("SELECT wid, name, url FROM webradio ORDER BY wid")

    @query_decorator("none")
    def add_webradios(self, cursor, values):
        query = "INSERT INTO webradio(wid,name,url)VALUES(%s,%s,%s)"
        cursor.executemany(query,values)
        self.connection.commit()

    @query_decorator("none")
    def clear_webradios(self, cursor):
        cursor.execute("DELETE FROM webradio")
        self.connection.commit()

    #
    # Stat requests
    #
    @query_decorator("none")
    def record_mediadb_stats(self, cursor, type):
        values = []
        if type == "audio":
            # number of songs
            cursor.execute("SELECT COUNT(l.name) FROM library l, library_dir d\
                WHERE d.lib_type = 'audio' AND l.directory = d.id")
            values.append((cursor.fetchone()[0],"songs"))
            for tag in ("genre", "artist", "album"):
                cursor.execute("SELECT DISTINCT value FROM media_info\
                    WHERE ikey = %s", (tag,))
                values.append((len(cursor.fetchall()),tag+"s"))
        elif type == "video":
            cursor.execute("SELECT COUNT(l.name) FROM library l, library_dir d\
                WHERE d.lib_type = 'video' AND l.directory = d.id")
            values.append((cursor.fetchone()[0],"videos"))

        cursor.executemany("UPDATE stats SET value = %s WHERE name = %s",values)

    @query_decorator("none")
    def set_update_time(self, cursor, type):
        cursor.execute("UPDATE stats SET value = %s WHERE name = %s",\
                                        (time.time(),type+"_library_update"))

    @query_decorator("custom")
    def get_update_time(self, cursor, type):
        cursor.execute("SELECT value FROM stats WHERE name = %s",\
                                                    (type+"_library_update",))
        (rs,) =  cursor.fetchone()
        return rs

    @query_decorator("fetchall")
    def get_stats(self, cursor):
        cursor.execute("SELECT * FROM stats")

    #
    # State requests
    #
    @query_decorator("none")
    def set_state(self, cursor, values):
        cursor.executemany("UPDATE variables SET value = %s WHERE name = %s" \
            ,values)
        self.connection.commit()

    @query_decorator("custom")
    def get_state(self, cursor, type):
        cursor.execute("SELECT value FROM variables WHERE name = %s",(type,))
        (rs,) =  cursor.fetchone()
        return rs

    def close(self):
        self.connection.close()

# vim: ts=4 sw=4 expandtab
