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


import os
from testdeejayd import TestCaseWithMediaData
from testdeejayd.db.schemas import SCHEMAS
from deejayd import DeejaydError
from deejayd.database.schema import DB_SCHEMA
from deejayd.database.connection import DatabaseConnection
from deejayd.server.core import DeejayDaemonCore


class TestDatabase(TestCaseWithMediaData):

    def setUp(self):
        self.dbfilename = '/tmp/testdeejayddb-' + \
                            self.testdata.getRandomString() + '.db'
        self.config.set('database', 'db_name', self.dbfilename)

    def tearDown(self):
        if os.path.isfile(self.dbfilename):
            os.unlink(self.dbfilename)

    def __init_db(self, version):
        if version in SCHEMAS:
            return DatabaseConnection(config=self.config, schema=SCHEMAS[version])
        raise DeejaydError("db version %d not found" % version)

    def test_migration_14(self):
        self.__init_db(14)
        # record a local webradio
        wb_category = self.testdata.getRandomString()
        wb_name = self.testdata.getRandomString()
        SQL = [
            "INSERT INTO webradio_source (id, name) VALUES(1,'local');",
            "INSERT INTO webradio_categories (id, source_id, name) VALUES(1, 1,'%s');" % wb_category,
            "INSERT INTO webradio (id, source_id, cat_id, name) VALUES(1, 1, 1, '%s');" % wb_name,
            "INSERT INTO webradio_entries (webradio_id, url) VALUES(1, '%s');" % "http://example.com",
        ]
        cursor = DatabaseConnection().cursor()
        for query in SQL:
            cursor.execute(query)
        DatabaseConnection().commit()
        DatabaseConnection().upgrade(self.config, cursor, DB_SCHEMA["version"],
                                     14)
        cursor.close()

        deejayd = DeejayDaemonCore(start_inotify=False)
        categories = deejayd.webradio.get_source_categories("local")
        self.assertEqual(len(categories), 1)
        self.assertTrue(wb_category in categories)

        deejayd.webradio.set_source_categorie(categories[wb_category])
        webradios = deejayd.webradio.get()["medias"]
        self.assertEqual(len(webradios), 1)
        self.assertEqual(webradios[0]["title"], wb_name)

        import kaa
        deejayd.close()
        kaa.main.stop()

# vim: ts=4 sw=4 expandtab
