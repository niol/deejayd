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

"""
 Class and methods to manage database
"""

from deejayd.ui import log
from deejayd.database import schema
from os import path
import sys

class OperationalError(Exception): pass

class UnknownDatabase:
    connection = None
    cursor = None

    def connect(self):
        raise NotImplementedError

    def execute(self,cur,query,parm = None):
        raise NotImplementedError

    def executemany(self,cur,query,parm):
        raise NotImplementedError

    def get_new_connection(self):
        raise NotImplementedError

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()


class Database(UnknownDatabase):

    def __init__(self):
        self.structure_created = False

    def init_db(self):
        for table in schema.db_schema:
            for stmt in self.to_sql(table):
                self.execute(stmt)
        log.info(_("Database structure successfully created."))
        for query in schema.db_init_cmds:
            self.execute(query)
        log.info(_("Initial entries correctly inserted."))
        self.structure_created = True
        self.connection.commit()

    def verify_database_version(self):
        try:
            self.execute("SELECT value FROM variables\
                WHERE name = 'database_version'", raise_exception = True)
            (db_version,) = self.cursor.fetchone()
            db_version = int(db_version)
        except OperationalError:
            self.init_db()
        else:
            if schema.db_schema_version > db_version:
                log.info(_("The database structure needs to be updated..."))

                base = path.dirname(__file__)
                base_import = "deejayd.database.upgrade"
                i = db_version+1
                while i < schema.db_schema_version+1:
                    db_file = "db_%d" % i
                    try: up = __import__(base_import+"."+db_file, {}, {}, base)
                    except ImportError:
                        err = _("Unable to upgrade database, have to quit")
                        log.err(err, True)
                    up.upgrade(self.cursor)
                    i += 1

                self.connection.commit()
                log.msg(_("The database structure has been updated"))

    #
    # Common MediaDB requests
    #
    def insert_file(self, dir, filename):
        query = "INSERT INTO library (directory,name)VALUES(%s, %s)"
        self.execute(query, (dir, filename))
        self.execute("SELECT id FROM library WHERE directory=%s AND name=%s",\
                        (dir, filename))
        (id,) = self.cursor.fetchone()
        return id

    def set_media_infos(self, file_id, infos):
        query = "REPLACE INTO media_info (id,ikey,value)VALUES(%s,%s,%s)"
        entries = [(file_id, k, v) for k, v in infos.items()]
        self.executemany(query, entries)

    def remove_file(self, id):
        queries = [
            "DELETE FROM library WHERE id = %s",
            "DELETE FROM media_info WHERE id = %s",
            "DELETE FROM medialist_libraryitem WHERE libraryitem_id = %s",
            ]
        for q in queries: self.execute(q, (id,))

    def is_file_exist(self, dirname, filename, type = "audio"):
        query = "SELECT d.id, l.id \
            FROM library l JOIN library_dir d ON d.id=l.directory\
            WHERE l.name = %s AND d.name = %s AND d.lib_type = %s"
        self.execute(query,(filename, dirname, type))
        rs = self.cursor.fetchone()
        return rs

    def erase_empty_dir(self, type = "audio"):
        self.execute("SELECT DISTINCT name FROM library_dir WHERE lib_type=%s",\
            (type,))
        for (dirname,) in self.cursor.fetchall():
            rs = self.get_all_files(dirname, type)
            if len(rs) == 0: # remove directory
                self.execute("DELETE FROM library_dir WHERE name = %s",\
                    (dirname,))

    def insert_dir(self, new_dir, type="audio"):
        query = "INSERT INTO library_dir (name,type,lib_type)VALUES(%s,%s,%s)"
        self.execute(query, (new_dir, 'directory', type))
        return self.is_dir_exist(new_dir, type)

    def remove_dir(self, id):
        self.execute("SELECT id FROM library WHERE directory = %s", (id,))
        for (id,) in self.cursor.fetchall():
            self.remove_file(id)
        self.execute("DELETE FROM library_dir WHERE id = %s", (id,))

    def remove_recursive_dir(self, dir, type="audio"):
        for file in self.get_all_files(dir, type):
            self.remove_file(file[2])
        self.execute("DELETE FROM library_dir\
                      WHERE name LIKE %s AND lib_type = %s", (dir+"%%", type))

    def is_dir_exist(self, dirname, type):
        self.execute("SELECT id FROM library_dir WHERE name=%s AND lib_type=%s"\
            ,(dirname, type))
        rs = self.cursor.fetchone()
        return rs and rs[0]

    def insert_dirlink(self, new_dirlink, type="audio"):
        query = "INSERT INTO library_dir (name,type,lib_type)VALUES(%s,%s,%s)"
        self.execute(query, (new_dirlink, "dirlink", type))

    def remove_dirlink(self, dirlink, type="audio"):
        query = "DELETE FROM library_dir WHERE name = %s AND lib_type = %s"
        self.execute(query, (dirlink, type))

    def get_dir_list(self, dir, type = "audio"):
        query = "SELECT DISTINCT id, name FROM library_dir\
            WHERE name LIKE %s AND lib_type = %s ORDER BY name"
        term = dir == "" and "%%" or dir+"/%%"
        self.execute(query, (term, type))
        return self.cursor.fetchall()

    def get_file_info(self, file_id, info_type):
        query = "SELECT value FROM media_info WHERE id = %s AND ikey = %s"
        self.execute(query, (file_id, info_type))
        return self.cursor.fetchone()

    def get_all_files(self, dir, type = "audio"):
        query = "SELECT DISTINCT d.id, d.name, l.id, l.name\
            FROM library l JOIN library_dir d ON d.id=l.directory\
            WHERE d.name LIKE %s AND d.lib_type = %s ORDER BY d.name,l.name"
        self.execute(query,(dir+"%%", type))
        return self.cursor.fetchall()

    def get_all_dirs(self, dir, type = "audio"):
        query = "SELECT DISTINCT id,name FROM library_dir\
            WHERE name LIKE %s AND type='directory' AND lib_type = %s\
            ORDER BY name"
        self.execute(query,(dir+"%%", type))
        return self.cursor.fetchall()

    def get_all_dirlinks(self, dirlink, type = 'audio'):
        query = "SELECT DISTINCT id,name FROM library_dir\
            WHERE name LIKE %s AND type='dirlink' AND lib_type = %s\
            ORDER BY name"
        self.execute(query,(dirlink+"%%", type))
        return self.cursor.fetchall()

    def _build_media_query(self, infos_list):
        selectquery = ""
        joinquery = ""
        for index, key in enumerate(infos_list):
            selectquery += ",i%d.value" % index
            joinquery += " JOIN media_info i%d ON i%d.id=i.id AND\
                i%d.ikey='%s'" % (index, index, index, key)
        return selectquery, joinquery

    def get_dir_content(self, dir, infos_list, type = "audio"):
        selectquery, joinquery = self._build_media_query(infos_list)
        query = "SELECT DISTINCT d.id, d.name, l.id, l.name"+ selectquery +\
            " FROM library l JOIN library_dir d ON d.id=l.directory\
                           JOIN media_info i ON i.id=l.id"\
                           + joinquery+\
            " WHERE d.name = %s AND d.lib_type = %s ORDER BY d.name,l.name"
        self.execute(query,(dir, type))
        return self.cursor.fetchall()

    def get_file(self, dir, file, infos_list, type = "audio"):
        selectquery, joinquery = self._build_media_query(infos_list)
        query = "SELECT DISTINCT d.id, d.name, l.id, l.name"+ selectquery +\
            " FROM library l JOIN library_dir d ON d.id=l.directory\
                           JOIN media_info i ON i.id=l.id"\
                           + joinquery+\
            " WHERE d.name = %s AND l.name = %s AND d.lib_type = %s"
        self.execute(query, (dir, file, type))
        return self.cursor.fetchall()

    def get_alldir_files(self, dir, infos_list, type = "audio"):
        selectquery, joinquery = self._build_media_query(infos_list)
        query = "SELECT DISTINCT d.id, d.name, l.id, l.name"+ selectquery +\
            " FROM library l JOIN library_dir d ON d.id=l.directory\
                           JOIN media_info i ON i.id=l.id"\
                           + joinquery+\
            " WHERE d.name LIKE %s AND d.lib_type = %s ORDER BY d.name,l.name"
        self.execute(query,(dir+"%%", type))
        return self.cursor.fetchall()

    def search(self, type, content, infos_list):
        selectquery, joinquery = self._build_media_query(infos_list)
        query = "SELECT DISTINCT d.id, d.name, l.id, l.name"+ selectquery +\
            " FROM library l JOIN library_dir d ON d.id=l.directory\
                           JOIN media_info i ON i.id=l.id"\
                           + joinquery+\
            " WHERE i.ikey=%s AND i.value LIKE %s ORDER BY d.name, l.name"
        self.execute(query,(type, "%%"+content+"%%"))
        return self.cursor.fetchall()

    #
    # static medialist requests
    #
    def get_static_medialist(self, name, infos_list):
        selectquery, joinquery = self._build_media_query(infos_list)
        query = "SELECT DISTINCT d.id, d.name, l.id, l.name"+ selectquery +\
            " FROM medialist m JOIN medialist_libraryitem mi\
                                    ON m.id = mi.medialist_id\
                           JOIN library l ON l.id = mi.libraryitem_id\
                           JOIN library_dir d ON d.id=l.directory\
                           JOIN media_info i ON i.id=l.id"\
                           + joinquery+\
            " WHERE m.name = %s AND m.type = 'static' ORDER BY mi.position"
        self.execute(query,(name,))
        return self.cursor.fetchall()

    def delete_static_medialist(self, name):
        # get id of medialist entries
        query = "SELECT id FROM medialist WHERE name=%s AND type = 'static'"
        self.execute(query ,(name,))
        try: (id,) = self.cursor.fetchone()
        except (IndexError, TypeError): return # medialist does not exist
        # remove medialist entries
        self.execute("DELETE FROM medialist_libraryitem\
            WHERE medialist_id = %s",(id,))
        self.execute("DELETE FROM medialist WHERE id = %s",(id,))
        self.connection.commit()

    def set_static_medialist(self, name, content):
        slt_query = "SELECT id FROM medialist WHERE name=%s AND type = 'static'"
        self.execute(slt_query, (name,))
        rs = self.cursor.fetchone()
        if not rs:
            query = "INSERT INTO medialist (name,type)VALUES(%s,'static')"
            self.execute(query, (name,))
            self.connection.commit()
            self.execute(slt_query,(name,))
            (id,) = self.cursor.fetchone()
        else: (id,) = rs

        self.execute(\
            "DELETE FROM medialist_libraryitem WHERE medialist_id = %s",(id,))
        values = [(id, s["media_id"]) for s in content]
        query = "INSERT INTO medialist_libraryitem(medialist_id,libraryitem_id)\
            VALUES(%s,%s)"
        self.executemany(query,values)
        self.connection.commit()

    def get_medialist_list(self, type = 'static'):
        query = "SELECT DISTINCT name FROM medialist WHERE type = %s"
        self.execute(query, (type,))
        return self.cursor.fetchall()

    #
    # Webradio requests
    #
    def get_webradios(self):
        self.execute("SELECT wid, name, url FROM webradio ORDER BY wid")
        return self.cursor.fetchall()

    def add_webradios(self,values):
        query = "INSERT INTO webradio(wid,name,url)VALUES(%s,%s,%s)"
        self.executemany(query,values)
        self.connection.commit()

    def clear_webradios(self):
        self.execute("DELETE FROM webradio")
        self.connection.commit()

    #
    # Stat requests
    #
    def record_mediadb_stats(self, type):
        values = []
        if type == "audio":
            # number of songs
            self.execute("SELECT COUNT(l.name) FROM library l, library_dir d\
                WHERE d.lib_type = 'audio' AND l.directory = d.id")
            values.append((self.cursor.fetchone()[0],"songs"))
            for tag in ("genre", "artist", "album"):
                self.execute("SELECT DISTINCT value FROM media_info\
                    WHERE ikey = %s", (tag,))
                values.append((len(self.cursor.fetchall()),tag+"s"))
        elif type == "video":
            self.execute("SELECT COUNT(l.name) FROM library l, library_dir d\
                WHERE d.lib_type = 'video' AND l.directory = d.id")
            values.append((self.cursor.fetchone()[0],"videos"))

        self.executemany("UPDATE stats SET value = %s WHERE name = %s",values)

    def set_update_time(self,type):
        import time
        self.execute("UPDATE stats SET value = %s WHERE name = %s",\
                                        (time.time(),type+"_library_update"))

    def get_update_time(self,type):
        self.execute("SELECT value FROM stats WHERE name = %s",\
                                                    (type+"_library_update",))
        (rs,) =  self.cursor.fetchone()
        return rs

    def get_stats(self):
        self.execute("SELECT * FROM stats")
        return self.cursor.fetchall()

    #
    # State requests
    #
    def set_state(self,values):
        self.executemany("UPDATE variables SET value = %s WHERE name = %s" \
            ,values)
        self.connection.commit()

    def get_state(self,type):
        self.execute("SELECT value FROM variables WHERE name = %s",(type,))
        (rs,) =  self.cursor.fetchone()

        return rs

# vim: ts=4 sw=4 expandtab
