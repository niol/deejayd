"""Deejayd Client library testing"""
from testdeejayd import TestCaseWithMediaData

from testdeejayd.server import TestServer
from deejayd.net.client import DeejayDaemon, DeejaydError

import threading


class TestClient(TestCaseWithMediaData):
    """Completely test the DeejaydClient library"""

    def setUp(self):
        TestCaseWithMediaData.setUp(self)
        self.testdata.build_audio_library_directory_tree()

        # Set up the test server
        testServerPort = 23344
        dbfilename = '/tmp/testdeejayddb-' +\
                     self.testdata.getRandomString() + '.db'
        self.testserver = TestServer(testServerPort,
                                     self.testdata.getRootDir(), dbfilename)
        self.testserver.start()

        # Instanciate the server object of the client library
        self.deejaydaemon = DeejayDaemon(False)
        self.deejaydaemon.connect('localhost', testServerPort)

    def testPing(self):
        """Ping server"""
        self.failUnless(self.deejaydaemon.ping().get_contents())

    def testPingAsync(self):
        """Ping server asynchroneously"""
        self.deejaydaemon.set_async(True)
        ans = self.deejaydaemon.ping()
        self.failUnless(ans.get_contents(),
                        'Server did not respond well to ping.')
        self.deejaydaemon.set_async(False)

    def test_answer_callback(self):
        """Ping server asynchroneously and check for the callback to be triggered"""
        cb_called = threading.Event()
        def tcb(answer):
            cb_called.set()

        self.deejaydaemon.set_async(True)

        ans = self.deejaydaemon.ping()
        ans.add_callback(tcb)
        # some seconds should be enough for the callback to be called
        cb_called.wait(4)
        self.failUnless(cb_called.isSet(), 'Answer callback was not triggered.')

        self.deejaydaemon.set_async(False)

    def tearDown(self):
        self.deejaydaemon.disconnect()
        self.testserver.stop()
        TestCaseWithMediaData.tearDown(self)

    def testSetMode(self):
        """Test setMode command"""

        # ask an unknown mode
        mode_name = self.testdata.getRandomString()
        self.assertRaises(DeejaydError, self.deejaydaemon.set_mode, mode_name) 

        # ask a known mode
        known_mode = 'playlist'
        ans = self.deejaydaemon.set_mode(known_mode)
        self.failUnless(ans.get_contents(),
                        'Server did not respond well to setMode command.')

        # Test if the mode has been set
        status = self.deejaydaemon.get_status()
        self.assertEqual(status['mode'], known_mode)

    def testPlaylistSaveRetrieve(self):
        """Save a playlist and try to retrieve it."""

        pl = []
        djplname = self.testdata.getRandomString()

        # Get current playlist
        djpl = self.deejaydaemon.get_current_playlist()
        self.assertEqual(djpl.get_contents(), [])

        # Add songs to playlist
        howManySongs = 3
        for songPath in self.testdata.getRandomSongPaths(howManySongs):
            pl.append(songPath)
            self.failUnless(djpl.add_song(songPath).get_contents())

        # Check for the playlist to be of appropriate length
        self.assertEqual(self.deejaydaemon.get_status()['playlistlength'],
                         howManySongs)

        # Save the playlist
        self.failUnless(djpl.save(djplname).get_contents())

        # Check for the saved playslit to be available
        retrievedPls = self.deejaydaemon.get_playlist_list().get_contents()
        self.failUnless(djplname in [p["name"] for p in retrievedPls])

        # Retrieve the saved playlist
        retrievedPl = self.deejaydaemon.get_playlist(djplname)
        for song_nb in range(len(pl)):
            self.assertEqual(pl[song_nb], retrievedPl[song_nb]['path'])

    def testWebradioAddRetrieve(self):
        """Save a webradio and check it is in the list, then delete it."""

        wrList = self.deejaydaemon.get_webradios()

        # Test for bad URI and inexistant playlist
        for badURI in [[self.testdata.getRandomString(50)],
                       ['http://' +\
                        self.testdata.getRandomString(50) + '.pls']]:
            self.assertRaises(DeejaydError, wrList.add_webradio,
                                            self.testdata.getRandomString(),
                                            badURI[0])
            # FIXME : provision for the future where the same webradio may have
            # multiple urls.
            #                                 badURI)


        testWrName = self.testdata.getRandomString()

        # FIXME : provision for the future where the same webradio may have
        # multiple urls.
        # testWrUrls = []
        # for urlCount in range(self.testdata.getRandomInt(10)):
        #     testWrUrls.append('http://' + self.testdata.getRandomString(50))
        testWrUrls = 'http://' + self.testdata.getRandomString(50)

        ans = wrList.add_webradio(testWrName, testWrUrls)
        self.failUnless(ans.get_contents())

        wrList = self.deejaydaemon.get_webradios()

        # FIXME : This should not be, see the future of webradios.
        testWrName += '-1'

        self.failUnless(testWrName in self.deejaydaemon.get_webradios().names())

        retrievedWr1 = wrList.get_webradio(testWrName)
        retrievedWr2 = self.deejaydaemon.get_webradios().\
                                                    get_webradio(testWrName)

        for retrievedWr in [retrievedWr1, retrievedWr2]:
            # FIXME : Same provision for the future.
            # for url in testWrUrls:
            #     self.failUnless(url in retrievedWr['Url'])
            self.assertEqual(testWrUrls, retrievedWr['url'])

        wrList.delete_webradio(testWrName)
        wrList = self.deejaydaemon.get_webradios()
        self.failIf(testWrName in wrList.names())


# vim: ts=4 sw=4 expandtab
