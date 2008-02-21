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

import sys
from ConfigParser import NoOptionError

def init(config):
    db_type =  config.get("database","db_type")

    if db_type == "sqlite":
        db_file = config.get("database","db_name")

        from deejayd.database.sqlite import SqliteDatabase
        return SqliteDatabase(db_file)
    elif db_type == "mysql":
        db_name = config.get("database","db_name")
        db_user = config.get("database","db_user")
        db_password = config.get("database","db_password")
        try: db_host = config.get("database","db_host")
        except NoOptionError:
            db_host = ""
        try: db_port = config.getint("database","db_port")
        except (NoOptionError, ValueError):
            db_port = 3306

        from deejayd.database.mysql import MysqlDatabase
        return MysqlDatabase(db_name, db_user, db_password, db_host, db_port)
    else:
        sys.exit(_("You chose a database which is not supported.\
                    Verify your config file."))

    return database

# vim: ts=4 sw=4 expandtab
