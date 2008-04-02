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

from deejayd.ui import log
from deejayd.database._base import Database, OperationalError
from pysqlite2 import dbapi2 as sqlite
from os import path


LOCK_TIMEOUT = 600


def str_encode(data):
    if isinstance(data, unicode):
        return data.encode("utf-8")
    return data


class SqliteDatabase(Database):

    def __init__(self, db_file):
        Database.__init__(self)
        self.db_file = path.expanduser(db_file)

    def connect(self):
        # Check pysqlite version
        pysqlite_min_version = [2, 2]
        pysqlite_version = map(int, sqlite.version.split('.'))
        if pysqlite_version < pysqlite_min_version:
            sqlite_error=_(\
                'This program requires pysqlite version %s or later.')\
                % '.'.join(map(str, pysqlite_min_version))
            log.err(sqlite_error, fatal = True)

        try:
            self.connection = sqlite.connect(self.db_file, timeout=LOCK_TIMEOUT)
        except sqlite.Error:
            error = _("Could not connect to sqlite database %s." % self.db_file)
            log.err(error, fatal = True)
        else:
            self.cursor = self.connection.cursor()

        # configure connection
        self.connection.text_factory = str
        self.connection.row_factory = sqlite.Row
        sqlite.register_adapter(str,str_encode)

        self.verify_database_version()

    def get_new_connection(self):
        return SqliteDatabase(self.db_file)

    def reset_connection(self):
        self.cursor.close()
        self.connection.close()
        self.connection = sqlite.connect(self.db_file, timeout=LOCK_TIMEOUT)
        self.cursor = self.connection.cursor()

    def execute(self, query, parm = None, raise_exception = False):
        if parm: query = query % (('?',) * len(parm))
        args = parm or ()
        try: self.cursor.execute(query,args)
        except sqlite.DatabaseError, err:
            self.reset_connection()
            log.err(_("Unable to execute database request '%s': %s") \
                        % (query, err))
            if raise_exception:
                raise OperationalError

    def executemany(self, query, parm = []):
        if parm == []: return # no request to execute
        query = query % (('?',) * len(parm[0]))
        try: self.cursor.executemany(query, parm)
        except sqlite.DatabaseError, err:
            self.reset_connection()
            log.err(_("Unable to execute database request '%s': %s") \
                        % (query, err))

    def to_sql(self, table):
        sql = ["CREATE TABLE %s (" % table.name]
        coldefs = []
        for column in table.columns:
            ctype = column.type.lower()
            if column.auto_increment:
                ctype = "integer PRIMARY KEY"
            elif len(table.key) == 1 and column.name in table.key:
                ctype += " PRIMARY KEY"
            elif ctype == "int":
                ctype = "integer"
            coldefs.append("    %s %s" % (column.name, ctype))
        if len(table.key) > 1:
            coldefs.append("    UNIQUE (%s)" % ','.join(table.key))
        sql.append(',\n'.join(coldefs) + '\n);')
        yield '\n'.join(sql)
        for index in table.indices:
            yield "CREATE INDEX %s_%s_idx ON %s (%s);" % (table.name,
                  '_'.join(index.columns), table.name, ','.join(index.columns))

    def init_db(self):
        Database.init_db(self)
        self.connection.commit()

        ####################################################################
        # workaround to migrate old database schema
        # remove it when it becomes useless
        ####################################################################
        try:
            self.execute("SELECT value FROM rj_variables\
                WHERE name = 'database_version'", raise_exception = True)
        except OperationalError:
            pass
        else: # old schema exists
            log.msg("Migrate from old database schema")
            # migrate audio library
            self.execute("SELECT * FROM rj_audio_library")
            library = self.cursor.fetchall()
            query = "INSERT INTO audio_library(dir,filename,type,title,\
                artist,album,genre,tracknumber,date,length,bitrate)VALUES \
                (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            self.executemany(query, library)

            # migrate video library
            self.execute("SELECT * FROM rj_video_library")
            library = self.cursor.fetchall()
            query = "INSERT INTO video_library(dir,filename,type,title,\
                length,videowidth,videoheight,subtitle) \
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
            self.executemany(query, library)

            # migrate medialist
            self.execute("SELECT * FROM rj_medialist")
            medialist = self.cursor.fetchall()
            for (n, pos, dir, fn) in medialist:
                self.execute("SELECT id FROM audio_library WHERE \
                    dir = %s AND filename = %s", (dir, fn))
                song = self.cursor.fetchone()
                try: id = song[0]
                except (IndexError, TypeError):
                    continue
                self.execute("INSERT INTO medialist(name,position,media_id)\
                    VALUES(%s,%s,%s)", (n, pos, id))

            # migrate webradio
            self.execute("SELECT * FROM rj_webradio")
            webradios = self.cursor.fetchall()
            self.executemany("INSERT INTO webradio(wid,name,url)\
                VALUES(%s,%s,%s)", webradios)

            # migrate stats
            self.execute("SELECT * FROM rj_stats")
            stats = self.cursor.fetchall()
            for (k, v) in stats:
                self.execute("UPDATE stats SET value = %s WHERE name = %s",\
                    (v,k))

            # remove old table
            self.execute("DROP TABLE rj_audio_library")
            self.execute("DROP TABLE rj_video_library")
            self.execute("DROP TABLE rj_webradio")
            self.execute("DROP TABLE rj_medialist")
            self.execute("DROP TABLE rj_variables")
            self.execute("DROP TABLE rj_stats")

            self.connection.commit()
        ####################################################################

# vim: ts=4 sw=4 expandtab
