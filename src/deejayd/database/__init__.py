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

from ConfigParser import NoOptionError
from deejayd.ui import log
from deejayd.database.queries import DatabaseQueries
from deejayd.database import schema

DatabaseError = None

def init(config):
    global DatabaseError

    db_type =  config.get("database","db_type")
    db_name = config.get("database","db_name")
    if db_type == "sqlite":
        from deejayd.database.backends import sqlite
        connection = sqlite.DatabaseWrapper(db_name)
        DatabaseError = sqlite.DatabaseError

    elif db_type == "mysql":
        db_user = config.get("database","db_user")
        db_password = config.get("database","db_password")
        try: db_host = config.get("database","db_host")
        except NoOptionError:
            db_host = ""
        try: db_port = config.getint("database","db_port")
        except (NoOptionError, ValueError):
            db_port = 3306

        from deejayd.database.backends import mysql
        connection = mysql.DatabaseWrapper(db_name, db_user, db_password,\
            db_host, db_port)
        DatabaseError = mysql.DatabaseError

    else:
        log.err(_(\
      "You chose a database which is not supported. Verify your config file."),\
      fatal = True)

    # verify database version
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT value FROM variables\
                            WHERE name = 'database_version'")
        (db_version,) = cursor.fetchone()
        db_version = int(db_version)
    except DatabaseError: # initailise db
        for table in schema.db_schema:
            for stmt in connection.to_sql(table):
                cursor.execute(stmt)
        log.info(_("Database structure successfully created."))
        for query in schema.db_init_cmds:
            cursor.execute(query)
        log.info(_("Initial entries correctly inserted."))

        DatabaseQueries.structure_created = True
        connection.commit()
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
                up.upgrade(cursor)
                i += 1
            connection.commit()

    cursor.close()
    return DatabaseQueries(connection)

# vim: ts=4 sw=4 expandtab
