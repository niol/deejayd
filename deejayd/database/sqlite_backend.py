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

from deejayd.ui import log
from deejayd.utils import str_decode

try: from sqlite3 import dbapi2 as sqlite  # python 2.5
except ImportError:
    from pysqlite2 import dbapi2 as sqlite
    # Check pysqlite version
    pysqlite_min_version = [2, 2]
    pysqlite_version = map(int, sqlite.version.split('.'))
    if pysqlite_version < pysqlite_min_version:
        sqlite_error = _('This program requires pysqlite version %s or later.')\
            % '.'.join(map(str, pysqlite_min_version))
        log.err(sqlite_error, fatal=True)

def str_adapter(data):
    try: return str_decode(data)
    except UnicodeError:
        return data

class SQLiteCursorWrapper(sqlite.Cursor):

    def execute(self, query, params=()):
        #print "execute query %s - %s" % (query, params)
        query = self.convert_query(query, len(params))
        rs = sqlite.Cursor.execute(self, query, params)
        return rs

    def executemany(self, query, param_list):
        # print "execute query %s - %s" % (query, param_list)
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
        yield "CREATE %s INDEX %s_%s_idx ON %s (%s);" % (unique, table.name,
              '_'.join(index.columns), table.name, ','.join(index.columns))

custom_queries = [
    # extract from ANALYZE request
    "ANALYZE;",
    "INSERT INTO sqlite_stat1 VALUES('stats',\
            'sqlite_autoindex_stats_1','7 1');",
    "INSERT INTO sqlite_stat1 VALUES('variables',\
            'sqlite_autoindex_variables_1','18 1');",
    "INSERT INTO sqlite_stat1 VALUES('library_dir',\
            'library_dir_name_lib_type_idx','377 2 1');",
    ]

# vim: ts=4 sw=4 expandtab
