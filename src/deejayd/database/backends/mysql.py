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

from threading import local
from deejayd.ui import log
import MySQLdb as mysql

DatabaseError = mysql.DatabaseError

class DatabaseWrapper(local):

    def __init__(self, db_name, db_user, db_password, db_host, db_port):
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port

        self.connection = None

    def _valid_connection(self):
        if self.connection is not None:
            try:
                self.connection.ping()
                return True
            except DatabaseError:
                self.connection.close()
                self.connection = None
        return False

    def cursor(self):
        if not self._valid_connection():
            try: self.connection = mysql.connect(db=self.db_name,\
                  user=self.db_user, passwd=self.db_password,\
                  host=self.db_host, port=self.db_port, use_unicode=False)
            except DatabaseError, err:
                error = _("Could not connect to MySQL server %s." % err)
                log.err(error, fatal = True)
        cursor = self.connection.cursor()
        return cursor

    def commit(self):
        if self.connection is not None:
            self.connection.commit()

    def rollback(self):
        if self.connection is not None:
            try:
                self.connection.rollback()
            except mysql.NotSupportedError:
                pass

    def get_last_insert_id(self, cursor):
        return cursor.lastrowid

    def close(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None


def to_sql(table):

    def __collist(table, columns):
        cols = []
        limit = 333 / len(columns)
        if limit > 255:
            limit = 255
        for c in columns:
            name = '`%s`' % c
            table_col = filter((lambda x: x.name == c), table.columns)
            if len(table_col) == 1 and table_col[0].type.lower() == 'text':
                name += '(%s)' % limit
            # For non-text columns, we simply throw away the extra bytes.
            # That could certainly be optimized better, but for now let's KISS.
            cols.append(name)
        return ','.join(cols)

    sql = ['CREATE TABLE %s (' % table.name]
    coldefs = []
    for column in table.columns:
        ctype = column.type
        if ctype == "blob": ctype = "mediumblob"
        if column.auto_increment:
            ctype = 'INT UNSIGNED NOT NULL AUTO_INCREMENT'
            # Override the column type, as a text field cannot
            # use auto_increment.
            column.type = 'int'
        coldefs.append('    `%s` %s' % (column.name, ctype))
    if len(table.key) > 0:
        coldefs.append('    PRIMARY KEY (%s)' %
                       __collist(table, table.key))
    #sql.append(',\n'.join(coldefs) + '\n) ENGINE=InnoDB')
    sql.append(',\n'.join(coldefs) + '\n)')
    yield '\n'.join(sql)

    for index in table.indices:
        unique = index.unique and "UNIQUE" or ""
        yield 'CREATE %s INDEX %s_%s_idx ON %s (%s);' % (unique,table.name,
              '_'.join(index.columns), table.name,
              __collist(table, index.columns))

custom_queries = [
    "CREATE UNIQUE INDEX id_key_value_idx ON media_info\
        (id, ikey(64), value(64));",
    "CREATE INDEX key_value_idx ON media_info\
        (ikey(64), value(64));",
    ]

# vim: ts=4 sw=4 expandtab
