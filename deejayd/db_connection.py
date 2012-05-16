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

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import deejayd.models

class DatabaseConnection(object):
    __instance = None
    Session = scoped_session(sessionmaker())
    debug = False
    config = None

    @classmethod
    def Instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    def __init__(self):
        type, name, host = "sqlite", "/:memory:", ""
        if self.config is not None:
            type = self.config.get("database", "db_type")
            name = self.config.get("database", "db_name")

            host = self.config.get("database", "db_host", "")
            if host != "":
                user = self.config.get("database", "db_user")
                password = self.config.get("database", "db_password")
                host = "%s:%s@%s" % (user, password, host)
        self.uri = "%s://%s%s" % (type, host, name)

        # create engine based on config
        self.engine = create_engine(self.uri, echo=self.debug)

        # create table
        base = deejayd.models.Base
        base.metadata.create_all(self.engine)

        # configure scoped session
        self.Session.configure(bind=self.engine)

    def get_session(self):
        return self.Session()

    def get_uri(self):
        return self.uri

if __name__ == "__main__":
    DatabaseConnection.debug = True
    con = DatabaseConnection.Instance()
    ses = con.get_session()

    lib = deejayd.models.library.Library(name = u"video")
    ses.add(lib)

    ses.commit()

# vim: ts=4 sw=4 expandtab
