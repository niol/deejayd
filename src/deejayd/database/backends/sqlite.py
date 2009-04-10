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

from os import path
from threading import local
from deejayd.ui import log

try: from sqlite3 import dbapi2 as sqlite # python 2.5
except ImportError:
    from pysqlite2 import dbapi2 as sqlite
    # Check pysqlite version
    pysqlite_min_version = [2, 2]
    pysqlite_version = map(int, sqlite.version.split('.'))
    if pysqlite_version < pysqlite_min_version:
        sqlite_error=_('This program requires pysqlite version %s or later.')\
            % '.'.join(map(str, pysqlite_min_version))
        log.err(sqlite_error, fatal = True)

LOCK_TIMEOUT = 600
DatabaseError = sqlite.DatabaseError

def str_encode(data):
    if isinstance(data, unicode):
        return data.encode("utf-8")
    return data


class DatabaseWrapper(local):

    def __init__(self, db_file):
        self._file = db_file
        self.connection = None

    def cursor(self):
        if self.connection is None:
            try: self.connection = sqlite.connect(self._file,\
                    timeout=LOCK_TIMEOUT)
            except sqlite.Error:
                error = _("Could not connect to sqlite database %s.")%self._file
                log.err(error, fatal = True)
            # configure connection
            sqlite.register_adapter(str,str_encode)

        return self.connection.cursor(factory = SQLiteCursorWrapper)

    def commit(self):
        if self.connection is not None:
            self.connection.commit()

    def rollback(self):
        if self.connection is not None:
            self.connection.rollback()

    def get_last_insert_id(self, cursor):
        return cursor.lastrowid

    def close(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None


class SQLiteCursorWrapper(sqlite.Cursor):

    def execute(self, query, params=()):
        query = self.convert_query(query, len(params))
        return sqlite.Cursor.execute(self, query, params)

    def executemany(self, query, param_list):
        if len(param_list) == 0: return
        query = self.convert_query(query, len(param_list[0]))
        return sqlite.Cursor.executemany(self, query, param_list)

    def convert_query(self, query, num_params):
        return query % tuple("?" * num_params)


def to_sql(table):
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
        unique = index.unique and "UNIQUE" or ""
        yield "CREATE %s INDEX %s_%s_idx ON %s (%s);" % (unique,table.name,
              '_'.join(index.columns), table.name, ','.join(index.columns))

custom_queries = [
    # custom indexes
    "CREATE INDEX id_key_value_1x ON media_info(id,ikey,value COLLATE BINARY);",
    "CREATE INDEX id_key_value_2x ON media_info(id,ikey,value COLLATE NOCASE);",
    "CREATE INDEX key_value_1x ON media_info (ikey, value COLLATE BINARY);",
    "CREATE INDEX key_value_2x ON media_info (ikey, value COLLATE NOCASE);",
    # extract from ANALYZE request
    "ANALYZE;",
    "INSERT INTO sqlite_stat1 VALUES('cover', 'cover_source_idx','208 1');",
    "INSERT INTO sqlite_stat1 VALUES('stats',\
            'sqlite_autoindex_stats_1','7 1');",
    "INSERT INTO sqlite_stat1 VALUES('variables',\
            'sqlite_autoindex_variables_1','18 1');",
    "INSERT INTO sqlite_stat1 VALUES('media_info',\
            'key_value_2x','70538 3713 6');",
    "INSERT INTO sqlite_stat1 VALUES('media_info',\
            'key_value_1x','70538 3713 6');",
    "INSERT INTO sqlite_stat1 VALUES('media_info',\
            'id_key_value_2x','70538 16 1 1');",
    "INSERT INTO sqlite_stat1 VALUES('media_info',\
            'id_key_value_1x','70538 16 1 1');",
    "INSERT INTO sqlite_stat1 VALUES('media_info',\
            'sqlite_autoindex_media_info_1','70538 16 1');",
    "INSERT INTO sqlite_stat1 VALUES('media_info',\
            'sqlite_autoindex_media_info_1','70538 16 1');",
    "INSERT INTO sqlite_stat1 VALUES('library',\
            'library_directory_idx','4421 18');",
    "INSERT INTO sqlite_stat1 VALUES('library',\
            'library_name_directory_idx','4421 2 1');",
    "INSERT INTO sqlite_stat1 VALUES('library_dir',\
            'library_dir_name_lib_type_idx','377 2 1');",
    ]

# vim: ts=4 sw=4 expandtab
