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

from testdeejayd import TestCaseWithData
from deejayd.database.sqlite import SqliteDatabase
import os

class testSqliteDatabase(TestCaseWithData):

    def setUp(self):
        TestCaseWithData.setUp(self)

        self.dbfilename = '/tmp/testdeejayddb-' + \
            self.testdata.getRandomString()
        self.db = SqliteDatabase(self.dbfilename)
        self.db.connect()

    def tearDown(self):
        TestCaseWithData.tearDown(self)
        self.db.close()
        os.remove(self.dbfilename)

    def testGetUnexistentPlaylist(self):
        """Unexistent playlist is zero rows"""
        randomName = self.testdata.getRandomString()
        self.assertEqual(self.db.get_audiolist(randomName), [])

    def testAddWebradio(self):
        """Add a webradio and retrieve it"""
        randomData = [(self.testdata.getRandomString(),
                        self.testdata.getRandomString(),
                        self.testdata.getRandomString())]

        self.db.add_webradios(randomData)

        for garbageWebradio in randomData:
            self.assert_(garbageWebradio in self.db.get_webradios())

# vim: ts=4 sw=4 expandtab
