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


    def testSaveAndRetrievePlaylist(self):
        """Save and retrieve playlist"""
        randomName = self.testdata.getRandomString()

        playlistContents = []

        i = 1
        for song in self.testdata.sampleLibrary[0:3]:
            playlistEntry = {}
            playlistEntry['pos'] = i
            playlistEntry['dir'] = os.path.dirname(song['filename'])
            playlistEntry['filename'] = os.path.basename(song['filename'])
            playlistContents.append(playlistEntry)
            i = i + 1
        self.db.save_medialist(playlistContents, randomName)

        retrievedPlaylist = self.db.get_audiolist(randomName)

        self.assertEqual(len(retrievedPlaylist), len(playlistContents))
        i = 0
        for retrievedPlaylistEntry in retrievedPlaylist:
            self.assertEqual(retrievedPlaylistEntry[0],
                            os.path.dirname(self.testdata.sampleLibrary[i]\
                            ['filename']))
            self.assertEqual(retrievedPlaylistEntry[1],
                            os.path.basename(self.testdata.sampleLibrary[i]\
                            ['filename']))
            self.assertEqual(retrievedPlaylistEntry[2], randomName)
            self.assertEqual(retrievedPlaylistEntry[3], i + 1)
            i = i + 1

    def testPlaylistManipulation(self):
        """Add, delete playlists and retrieve playlist list"""
        randomName = self.testdata.getRandomString()

        self.assertEqual(self.db.get_audiolist(randomName), [])

        playlistContents = [{ 'pos':0,
                                'dir': self.testdata.getRandomString(),
                                'filename': self.testdata.getRandomString()}]
        self.db.save_medialist(playlistContents, randomName)
        self.assertNotEqual(self.db.get_audiolist(randomName), [])
        self.assert_((randomName,) in self.db.get_medialist_list())

        anotherRandomName = self.testdata.getRandomString()
        self.db.save_medialist(playlistContents, anotherRandomName)

        self.db.delete_medialist(randomName)
        self.assertEqual(self.db.get_audiolist(randomName), [])
        self.assert_((randomName,) not in self.db.get_medialist_list())
        self.assert_((anotherRandomName,) in self.db.get_medialist_list())


    def testAddWebradio(self):
        """Add a webradio and retrieve it"""
        randomData = [(self.testdata.getRandomString(),
                        self.testdata.getRandomString(),
                        self.testdata.getRandomString())]

        self.db.add_webradios(randomData)

        for garbageWebradio in randomData:
            self.assert_(garbageWebradio in self.db.get_webradios())


# vim: ts=4 sw=4 expandtab
