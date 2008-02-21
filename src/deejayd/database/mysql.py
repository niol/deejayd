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
import MySQLdb as mysql
import sys


class MysqlDatabase(Database):

    def __init__(self, db_name, db_user, db_password, db_host, db_port):
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port

    def connect(self):
        try:
            self.connection = mysql.connect(db=self.db_name,\
                user=self.db_user, passwd=self.db_password,\
                host=self.db_host, port=self.db_port, use_unicode=False)
        except ValueError:
            error = _("Could not connect to MySQL server.")
            log.err(error)
            sys.exit(error)

        self.cursor = self.connection.cursor()
        self.verify_database_version()

    def get_new_connection(self):
        return MysqlDatabase(self.db_name, self.db_user, self.db_password, \
            self.db_host, self.db_port)

    def execute(self, query, parm = None, raise_exception = False):
        try: self.cursor.execute(query,parm)
        except (mysql.OperationalError, mysql.ProgrammingError), err:
            log.err(_("Unable to execute database request '%s': %s") \
                        % (query, err))
            if raise_exception:
                raise OperationalError

    def executemany(self, query, parm = []):
        if parm == []: # no request to execute
            return
        try: self.cursor.executemany(query,parm)
        except mysql.OperationalError, err:
            log.err(_("Unable to execute database request '%s': %s") \
                        % (query, err))

    def __collist(self, table, columns):
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

    def to_sql(self, table):
        sql = ['CREATE TABLE %s (' % table.name]
        coldefs = []
        for column in table.columns:
            ctype = column.type
            if column.auto_increment:
                ctype = 'INT UNSIGNED NOT NULL AUTO_INCREMENT'
                # Override the column type, as a text field cannot
                # use auto_increment.
                column.type = 'int'
            coldefs.append('    `%s` %s' % (column.name, ctype))
        if len(table.key) > 0:
            coldefs.append('    PRIMARY KEY (%s)' %
                           self.__collist(table, table.key))
        sql.append(',\n'.join(coldefs) + '\n)')
        yield '\n'.join(sql)

        for index in table.indices:
            yield 'CREATE INDEX %s_%s_idx ON %s (%s);' % (table.name,
                  '_'.join(index.columns), table.name,
                  self.__collist(table, index.columns))

# vim: ts=4 sw=4 expandtab
