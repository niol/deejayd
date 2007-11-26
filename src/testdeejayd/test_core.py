"""Deejayd Client library testing"""
import os, time, random

from testdeejayd import TestCaseWithMediaData

from deejayd.interfaces import DeejaydError
from deejayd.core import DeejayDaemonCore
from deejayd.ui.config import DeejaydConfig


class TestCore(TestCaseWithMediaData):
    """Test the deejayd daemon core."""

    def setUp(self):
        TestCaseWithMediaData.setUp(self)
        self.testdata.build_audio_library_directory_tree()

        config = DeejaydConfig()
        self.dbfilename = '/tmp/testdeejayddb-' +\
                          self.testdata.getRandomString() + '.db'
        config.set('database', 'db_file', self.dbfilename)

        config.set('mediadb', 'music_directory', self.testdata.getRootDir())
        config.set('mediadb', 'video_directory', self.testdata.getRootDir())

        self.deejaydcore = DeejayDaemonCore(config)
        self.deejaydcore.audio_library._update()

    def tearDown(self):
        os.unlink(self.dbfilename)
        TestCaseWithMediaData.tearDown(self)

    def testSetMode(self):
        """Test setMode command"""

        # ask an unknown mode
        mode_name = self.testdata.getRandomString()
        self.assertRaises(DeejaydError, self.deejaydcore.set_mode, mode_name)

        # ask a known mode
        known_mode = 'playlist'
        self.deejaydcore.set_mode(known_mode)

        # Test if the mode has been set
        status = self.deejaydcore.get_status()
        self.assertEqual(status['mode'], known_mode)

    def testPlaylistSaveRetrieve(self):
        """Save a playlist and try to retrieve it."""

        pl = []
        djplname = self.testdata.getRandomString()

        # Get current playlist
        djpl = self.deejaydcore.get_playlist()
        self.assertEqual(djpl.get().get_medias(), pl)

        self.assertRaises(DeejaydError, djpl.add_song,
                                        self.testdata.getRandomString())

        # Add songs to playlist
        howManySongs = 3
        for songPath in self.testdata.getRandomSongPaths(howManySongs):
            pl.append(songPath)
            djpl.add_song(songPath)

        # Check for the playlist to be of appropriate length
        self.assertEqual(self.deejaydcore.get_status()['playlistlength'],
                         howManySongs)

        djpl.save(djplname)

        # Check for the saved playslit to be available
        retrievedPls = self.deejaydcore.get_playlist_list()
        self.failUnless(djplname in retrievedPls)

        # Retrieve the saved playlist
        djpl = self.deejaydcore.get_playlist(djplname)
        retrievedPl = djpl.get().get_medias()
        for song_nb in range(len(pl)):
            self.assertEqual(pl[song_nb], retrievedPl[song_nb]['path'])

    def testWebradioAddRetrieve(self):
        """Save a webradio and check it is in the list, then delete it."""

        wr_list = self.deejaydcore.get_webradios()

        # Test for bad URI and inexistant playlist
        for badURI in [[self.testdata.getRandomString(50)],
                       ['http://' +\
                        self.testdata.getRandomString(50) + '.pls']]:
            self.assertRaises(DeejaydError, wr_list.add_webradio,
                                            self.testdata.getRandomString(),
                                            badURI[0])
            # FIXME : provision for the future where the same webradio may have
            # multiple urls.
            #                                badURI)

        testWrName = self.testdata.getRandomString()

        # FIXME : provision for the future where the same webradio may have
        # multiple urls.
        # testWrUrls = []
        # for urlCount in range(self.testdata.getRandomInt(10)):
        #     testWrUrls.append('http://' + self.testdata.getRandomString(50))
        testWrUrls = 'http://' + self.testdata.getRandomString(50)

        wr_list.add_webradio(testWrName, testWrUrls)

        # FIXME : This should not be, see the future of webradios.
        testWrName += '-1'

        self.failUnless(testWrName in self.deejaydcore.get_webradios().names())

        retrievedWr1 = wr_list.get_webradio(testWrName)
        retrievedWr2 = self.deejaydcore.get_webradios().\
                                                    get_webradio(testWrName)

        for retrievedWr in [retrievedWr1, retrievedWr2]:
            # FIXME : Same provision for the future.
            # for url in testWrUrls:
            #     self.failUnless(url in retrievedWr['Url'])
            self.assertEqual(testWrUrls, retrievedWr['url'])

        self.assertRaises(DeejaydError, wr_list.delete_webradio, 51)

        wr_list.delete_webradio(retrievedWr1['id'])
        wr_list = self.deejaydcore.get_webradios()
        self.failIf(testWrName in wr_list.names())

    def testQueue(self):
        """Add songs to the queue, try to retrieve it, delete some songs in it, then clear it."""
        q = self.deejaydcore.get_queue()

        myq = []
        how_many_songs = 10
        for song_path in self.testdata.getRandomSongPaths(how_many_songs):
            myq.append(song_path)
            q.add_song(song_path)

        ddq = q.get()

        ddq_paths = [song['path'] for song in ddq]
        for song_path in myq:
            self.failUnless(song_path in ddq_paths)

        random.seed(time.time())
        songs_to_delete = random.sample(myq, how_many_songs / 3)
        q.del_songs([song['id'] for song in ddq\
                                if song['path'] in songs_to_delete])

        ddq = q.get()
        ddq_paths = [song['path'] for song in ddq]
        for song_path in myq:
            if song_path in songs_to_delete:
                self.failIf(song_path in ddq_paths)
            else:
                self.failUnless(song_path in ddq_paths)

        q.clear()
        ddq = q.get()
        self.assertEqual(ddq, [])


# vim: ts=4 sw=4 expandtab
