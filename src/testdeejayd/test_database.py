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


import os, unittest

from testdeejayd import TestCaseWithData

from deejayd.mediafilters import *

import deejayd.database
import deejayd.ui.config
from deejayd.database.dbobjects import SQLizer


class TestDatabase(TestCaseWithData):

    def setUp(self):
        super(TestDatabase, self).setUp()

        config = deejayd.ui.config.DeejaydConfig()
        config.set('database', 'db_type', 'sqlite')
        dbfilename = self.testdata.getRandomString() + '.db'
        self.dbfilename = os.path.join('/tmp', dbfilename)
        config.set('database', 'db_name', self.dbfilename)
        self.db = deejayd.database.init(config)

        self.sqlizer = SQLizer()

    def tearDown(self):
        self.db.close()
        os.unlink(self.dbfilename)

    def test_basicfilter_save_retrieve(self):
        """Test the saving and retrieval of a basic filter"""
        f_class = self.testdata.getRandomElement(BASIC_FILTERS)
        f = f_class(self.testdata.getRandomString(),
                    self.testdata.getRandomString())
        sqlf = self.sqlizer.translate(f)

        fid = sqlf.save(self.db)
        self.db.connection.commit()

        cursor = self.db.connection.cursor()
        retrieved_filter = self.db.get_filter(cursor, fid)

        self.failUnless(f.equals(retrieved_filter))

        sqlf.tag = self.testdata.getRandomString()
        sqlf.save(self.db)
        self.db.connection.commit()

        retrieved_filter = self.db.get_filter(cursor, fid)
        self.failUnless(sqlf.equals(retrieved_filter))

        cursor.close()

    def test_complex_filter_save_retrieve(self):
        """Test the saving and retrieval of a complex filter"""
        f = self.testdata.get_sample_filter()
        sqlf = self.sqlizer.translate(f)

        fid = sqlf.save(self.db)
        self.db.connection.commit()

        cursor = self.db.connection.cursor()
        retrieved_filter = self.db.get_filter(cursor, fid)

        self.assert_filter_matches_sample(retrieved_filter)
        cursor.close()

    def test_magic_medialist_save_retrieve(self):
        """Test the saving and retrieval of a magic medialist"""
        f = self.testdata.get_sample_filter()

        pl_name = self.testdata.getRandomString()
        pl_id = self.db.set_magic_medialist_filters(pl_name, [f])

        # retrieve magic playlist
        retrieved_filters = self.db.get_magic_medialist_filters(pl_id)
        self.assertEqual(len(retrieved_filters), 1)
        self.failUnless(f.equals(retrieved_filters[0]))

        # resave the same playlist
        self.db.set_magic_medialist_filters(pl_name, retrieved_filters)

# vim: ts=4 sw=4 expandtab
