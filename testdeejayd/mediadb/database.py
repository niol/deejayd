from testdeejayd import TestCaseWithData
from deejayd.mediadb.database import sqliteDatabase
import os

class testSqliteDatabase(TestCaseWithData):

    def setUp(self):
        TestCaseWithData.setUp(self)

        self.dbfilename = '/tmp/testdeejayddb-' + self.testdata.getRandomString()
        self.db = sqliteDatabase(self.dbfilename)
        self.db.connect()

    def tearDown(self):
        TestCaseWithData.tearDown(self)

        self.db.close()

        os.remove(self.dbfilename)

    def testGetUnexistentPlaylist(self):
        """Unexistent playlist is zero rows"""
        randomName = self.testdata.getRandomString()
        self.assertEqual(self.db.getPlaylist(randomName), [])


    def testSaveAndRetrievePlaylist(self):
        """Save and retrieve playlist"""
        randomName = self.testdata.getRandomString()

        playlistContents = []

        i = 1
        for song in self.testdata.data[0:3]:
            playlistEntry = {}
            playlistEntry['Pos'] = i
            playlistEntry['dir'] = os.path.dirname(song['filename'])
            playlistEntry['filename'] = os.path.basename(song['filename'])
            playlistContents.append(playlistEntry)
            i = i + 1
        self.db.savePlaylist(playlistContents, randomName)

        retrievedPlaylist = self.db.getPlaylist(randomName)

        self.assertEqual(len(retrievedPlaylist), len(playlistContents))
        i = 0
        for retrievedPlaylistEntry in retrievedPlaylist:
            self.assertEqual(retrievedPlaylistEntry[0],
                            os.path.dirname(self.testdata.data[i]['filename']))
            self.assertEqual(retrievedPlaylistEntry[1],
                            os.path.basename(self.testdata.data[i]['filename']))
            self.assertEqual(retrievedPlaylistEntry[2], randomName)
            self.assertEqual(retrievedPlaylistEntry[3], i + 1)
            i = i + 1

    def testPlaylistManipulation(self):
        """Add, delete playlists and retrieve playlist list"""
        randomName = self.testdata.getRandomString()

        self.assertEqual(self.db.getPlaylist(randomName), [])

        playlistContents = [{ 'Pos':0,
                                'dir': self.testdata.getRandomString(),
                                'filename': self.testdata.getRandomString()}]
        self.db.savePlaylist(playlistContents, randomName)
        self.assertNotEqual(self.db.getPlaylist(randomName), [])
        self.assert_((randomName,) in self.db.getPlaylistList())

        anotherRandomName = self.testdata.getRandomString()
        self.db.savePlaylist(playlistContents, anotherRandomName)

        self.db.deletePlaylist(randomName)
        self.assertEqual(self.db.getPlaylist(randomName), [])
        self.assert_((randomName,) not in self.db.getPlaylistList())
        self.assert_((anotherRandomName,) in self.db.getPlaylistList())


# vim: ts=4 sw=4 expandtab
