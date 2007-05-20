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
        self.assertEqual(self.db.get_playlist(randomName), [])


    def testSaveAndRetrievePlaylist(self):
        """Save and retrieve playlist"""
        randomName = self.testdata.getRandomString()

        playlistContents = []

        i = 1
        for song in self.testdata.sampleLibrary[0:3]:
            playlistEntry = {}
            playlistEntry['Pos'] = i
            playlistEntry['dir'] = os.path.dirname(song['filename'])
            playlistEntry['filename'] = os.path.basename(song['filename'])
            playlistContents.append(playlistEntry)
            i = i + 1
        self.db.save_playlist(playlistContents, randomName)

        retrievedPlaylist = self.db.get_playlist(randomName)

        self.assertEqual(len(retrievedPlaylist), len(playlistContents))
        i = 0
        for retrievedPlaylistEntry in retrievedPlaylist:
            self.assertEqual(retrievedPlaylistEntry[0],
                            os.path.dirname(self.testdata.sampleLibrary[i]['filename']))
            self.assertEqual(retrievedPlaylistEntry[1],
                            os.path.basename(self.testdata.sampleLibrary[i]['filename']))
            self.assertEqual(retrievedPlaylistEntry[2], randomName)
            self.assertEqual(retrievedPlaylistEntry[3], i + 1)
            i = i + 1

    def testPlaylistManipulation(self):
        """Add, delete playlists and retrieve playlist list"""
        randomName = self.testdata.getRandomString()

        self.assertEqual(self.db.get_playlist(randomName), [])

        playlistContents = [{ 'Pos':0,
                                'dir': self.testdata.getRandomString(),
                                'filename': self.testdata.getRandomString()}]
        self.db.save_playlist(playlistContents, randomName)
        self.assertNotEqual(self.db.get_playlist(randomName), [])
        self.assert_((randomName,) in self.db.get_playlist_list())

        anotherRandomName = self.testdata.getRandomString()
        self.db.save_playlist(playlistContents, anotherRandomName)

        self.db.delete_playlist(randomName)
        self.assertEqual(self.db.get_playlist(randomName), [])
        self.assert_((randomName,) not in self.db.get_playlist_list())
        self.assert_((anotherRandomName,) in self.db.get_playlist_list())


    def testAddWebradio(self):
        """Add a webradio and retrieve it"""
        randomData = [(self.testdata.getRandomString(),
                        self.testdata.getRandomString(),
                        self.testdata.getRandomString())]

        self.db.add_webradios(randomData)

        for garbageWebradio in randomData:
            self.assert_(garbageWebradio in self.db.get_webradios())


# vim: ts=4 sw=4 expandtab
