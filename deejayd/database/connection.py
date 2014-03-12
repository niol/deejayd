# Deejayd, a media player daemon
# Copyright (C) 2007-2012 Mickael Royer <mickael.royer@gmail.com>
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
from deejayd.ui.config import DeejaydConfig
from deejayd.database import sqlite_backend
from deejayd.database.schema import DB_SCHEMA
from deejayd import Singleton
from deejayd import DeejaydError

LOCK_TIMEOUT = 600

@Singleton
class DatabaseConnection(local):
    """ Implementation of the db connection interface """
    structure_created = False

    def __init__(self, config=None, schema=DB_SCHEMA):
        self.schema = schema
        if config is None:
            config = DeejaydConfig()
        self.file = config.get("database", "db_name")
        self.connection = None

        # verify database version
        cursor = self.cursor()
        try:
            cursor.execute("SELECT value FROM variables\
                                WHERE name = 'database_version'")
            (db_version,) = cursor.fetchone()
            db_version = int(db_version)
        except DeejaydError:  # initailise db
            self.__create(cursor)
            self.structure_created = True
            self.connection.commit()
        else:
            if self.schema["version"] > db_version:
                self.upgrade(config, cursor, schema["version"], db_version)
        cursor.close()

    def cursor(self):
        if self.connection is None:
            self.__connect()
        return self.connection.cursor(\
                factory=sqlite_backend.SQLiteCursorWrapper)

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
            # save uncommited changes before to quit
            self.connection.commit()
            self.connection.close()
            self.connection = None
        DatabaseConnection.destroy()

    def __connect(self):
        if self.connection is None:
            try: self.connection = sqlite_backend.sqlite.connect(self.file, \
                    timeout=LOCK_TIMEOUT)
            except sqlite_backend.sqlite.Error:
                error = _("Could not connect to sqlite database %s.")\
                        % self.file
                log.err(error, fatal=True)
            # configure connection
            sqlite_backend.sqlite.register_adapter(str, \
                    sqlite_backend.str_adapter)

    def __create(self, cursor):
        for table in self.schema["tables"]:
            for stmt in sqlite_backend.to_sql(table):
                cursor.execute(stmt)
        for query in sqlite_backend.custom_queries:
            cursor.execute(query)
        log.info(_("Database structure successfully created."))
        for query in self.schema["initial_sql"]:
            cursor.execute(query)
        log.info(_("Initial entries correctly inserted."))

    def upgrade(self, config, cursor, db_schema_version, db_version):
        log.info(_("The database structure needs to be updated..."))

        base = path.dirname(__file__)
        base_import = "deejayd.database.upgrade"
        i = db_version + 1
        while i < db_schema_version + 1:
            db_file = "db_%d" % i
            try: up = __import__(base_import + "." + db_file, {}, {}, base)
            except ImportError:
                err = _("Unable to upgrade database, have to quit")
                log.err(err, True)
            up.upgrade(cursor, sqlite_backend, config)
            i += 1
        self.connection.commit()

# vim: ts=4 sw=4 expandtab