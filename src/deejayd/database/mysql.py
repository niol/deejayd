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


class MysqlDatabase(Database):

    def __init__(self, db_name, db_user, db_password, db_host, db_port):
        Database.__init__(self)
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port

        self.connection = None
        self.cursor = None

    def __connect(self):
        if self.connection is None:
            try:
                self.connection = mysql.connect(db=self.db_name,\
                      user=self.db_user, passwd=self.db_password,\
                      host=self.db_host, port=self.db_port, use_unicode=False)
                self.cursor = self.connection.cursor()
            except mysql.DatabaseError, err:
                error = _("Could not connect to MySQL server %s." % err)
                log.err(error, fatal = True)

    def connect(self):
        self.__connect()
        self.verify_database_version()

    def get_new_connection(self):
        return MysqlDatabase(self.db_name, self.db_user, self.db_password, \
            self.db_host, self.db_port)

    def __valid_connection(self):
        try: self.connection.ping()
        except mysql.DatabaseError:
            self.close()
            log.info(_("Try Mysql reconnection"))
            self.__connect()
            return False
        return True

    def __execute(self, func_name, query, parm, raise_exception = False):
        func = getattr(self.cursor, func_name)
        try: func(query,parm)
        except mysql.DatabaseError, err:
            if self.__valid_connection():
                log.err(_("Unable to execute database request '%s': %s") \
                        % (query, err))
                if raise_exception: raise OperationalError
            self.__execute(func_name, query, parm, raise_exception)

    def execute(self, query, parm = None, raise_exception = False):
        self.__execute("execute", query, parm, raise_exception)

    def executemany(self, query, parm = []):
        if parm == []: return # no request to execute
        self.__execute("executemany", query, parm)

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
        sql.append(',\n'.join(coldefs) + '\n) ENGINE=InnoDB')
        yield '\n'.join(sql)

        for index in table.indices:
            yield 'CREATE INDEX %s_%s_idx ON %s (%s);' % (table.name,
                  '_'.join(index.columns), table.name,
                  self.__collist(table, index.columns))

    def close(self):
        if self.cursor is not None:
            self.cursor.close()
            self.cursor = None
        if self.connection is not None:
            self.connection.close()
            self.connection = None

# vim: ts=4 sw=4 expandtab
