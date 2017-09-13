# Deejayd, a media player daemon
# Copyright (C) 2007-2017 Mickael Royer <mickael.royer@gmail.com>
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

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.engine.reflection import Inspector
import migrate.versioning.api
from deejayd.ui import log

# use scoped session to guarantee that one session is used per thread
Session = scoped_session(sessionmaker())


def init(uri, debug=False):
    repository = os.path.join(os.path.dirname(__file__), "dbmigrate")
    last_version = migrate.versioning.api.version(url=uri,
                                                  repository=repository)

    # create engine based on config
    log.debug("Connection to database %s" % uri)
    engine = create_engine(uri, echo=debug)

    # know if table as instantiated
    inspector = Inspector.from_engine(engine)
    if not inspector.get_table_names():
        log.msg("Create database tables...")
        # create table
        import deejayd.db.models
        base = deejayd.db.models.Base
        base.metadata.create_all(engine)
        # init migrate version to the last
        migrate.versioning.api.version_control(url=uri,
                                               repository=repository,
                                               version=last_version)
    else:
        try:
            vers = migrate.versioning.api.db_version(url=uri,
                                                     repository=repository)
        except:  # set db_version to 0
            migrate.versioning.api.version_control(url=uri,
                                                   repository=repository,
                                                   version=0)
            vers = 0
        if vers < last_version:
            log.msg("Upgrade database schema to %d" % last_version)
            migrate.versioning.api.upgrade(url=uri, repository=repository)

    # configure scoped session
    Session.configure(bind=engine)
