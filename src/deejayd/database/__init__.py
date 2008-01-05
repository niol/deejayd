# Deejayd, a media player daemon
# Copyright (C) 2007 Mickael Royer <mickael.royer@gmail.com>
#                    Alexandre Rossi <alexandre.rossi@gmail.com>
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

class DatabaseFactory:
    supported_database = ("sqlite")

    def __init__(self,config):
        self.config = config

        try: self.db_type =  config.get("database","db_type")
        except:
            raise SystemExit(\
                _("You do not choose a database. Verify your config file."))
        else:
            if self.db_type not in self.__class__.supported_database:
                raise SystemExit(\
     _("You chose a database which is not supported. Verify your config file."))

    def get_db(self):
        if self.db_type == "sqlite":
            db_file = self.config.get("database","db_file")
            try: prefix = self.config.get("database","db_prefix") + "_"
            except NoOptionError: prefix = ""

            from deejayd.database.sqlite import SqliteDatabase
            return SqliteDatabase(db_file,prefix)

        return None


def init(config):
    database = DatabaseFactory(config)
    return database

# vim: ts=4 sw=4 expandtab
