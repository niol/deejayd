"""Deejayd Client library testing"""
import threading

from testdeejayd import TestCaseWithMediaData

from testdeejayd.server import TestServer
from deejayd.net.client import DeejayDaemonSync, DeejayDaemonAsync, \
                               DeejaydError, DeejaydPlaylist


class TestSyncClient(TestCaseWithMediaData):
    """Test the DeejaydClient library in synchroneous mode."""

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
        self.deejaydaemon = DeejayDaemonSync()
        self.deejaydaemon.connect('localhost', testServerPort)

    def testPing(self):
        """Ping server"""
        self.failUnless(self.deejaydaemon.ping().get_contents())

    def tearDown(self):
        self.deejaydaemon.disconnect()
        self.testserver.stop()
        TestCaseWithMediaData.tearDown(self)

    def testSetMode(self):
        """Test setMode command"""

        # ask an unknown mode
        mode_name = self.testdata.getRandomString()
        ans = self.deejaydaemon.set_mode(mode_name)
        self.assertRaises(DeejaydError, ans.get_contents)

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
        djpl = DeejaydPlaylist(self.deejaydaemon)
        self.assertEqual(djpl.get().get_medias(), [])

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
        retrievedPls = self.deejaydaemon.get_playlist_list().get_medias()
        self.failUnless(djplname in [p["name"] for p in retrievedPls])

        # Retrieve the saved playlist
        djpl = DeejaydPlaylist(self.deejaydaemon, djplname)
        retrievedPl = djpl.get().get_medias()
        for song_nb in range(len(pl)):
            self.assertEqual(pl[song_nb], retrievedPl[song_nb]['path'])

    def testWebradioAddRetrieve(self):
        """Save a webradio and check it is in the list, then delete it."""

        wrList = self.deejaydaemon.get_webradios()

        # Test for bad URI and inexistant playlist
        for badURI in [[self.testdata.getRandomString(50)],
                       ['http://' +\
                        self.testdata.getRandomString(50) + '.pls']]:
            ans = wrList.add_webradio(self.testdata.getRandomString(),
                                      badURI[0])
            # FIXME : provision for the future where the same webradio may have
            # multiple urls.
            #                         badURI)
            self.assertRaises(DeejaydError, ans.get_contents)

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

class TestAsyncClient(TestCaseWithMediaData):
    """Test the DeejaydClient library in asynchroenous mode."""

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
        self.deejaydaemon = DeejayDaemonAsync()
        self.deejaydaemon.connect('localhost', testServerPort)

    def tearDown(self):
        self.deejaydaemon.disconnect()
        self.testserver.stop()
        TestCaseWithMediaData.tearDown(self)

    def test_ping(self):
        """Ping server asynchroneously"""
        ans = self.deejaydaemon.ping()
        self.failUnless(ans.get_contents(),
                        'Server did not respond well to ping.')

    def test_answer_callback(self):
        """Ping server asynchroneously and check for the callback to be triggered"""
        cb_called = threading.Event()
        def tcb(answer):
            cb_called.set()

        ans = self.deejaydaemon.ping()
        ans.add_callback(tcb)
        # some seconds should be enough for the callback to be called
        cb_called.wait(4)
        self.failUnless(cb_called.isSet(), 'Answer callback was not triggered.')

    def testPlaylistSaveRetrieve(self):
        """Test playlist commands asynchroneously and callback"""

        # Get current playlist and add callback
        self.pl = None
        cb_called = threading.Event()
        def tcb(answer):
            cb_called.set()
            self.pl = answer.get_medias()

        djpl = DeejaydPlaylist(self.deejaydaemon)
        djpl.get().add_callback(tcb)

        cb_called.wait(4)
        self.failUnless(cb_called.isSet(), 'Answer callback was not triggered.')
        self.assertEqual(self.pl, [])

        # Add songs to playlist and get status
        cb_called = threading.Event()
        self.should_stop = False
        self.status = None

        def tcb_status(answer):
            cb_called.set()
            self.status = answer.get_contents()
            self.should_stop = True

        def cb_update_status(answer):
            self.deejaydaemon.get_status().add_callback(tcb_status)

        djpl.add_song(self.testdata.getRandomSongPaths(1)[0]).\
                add_callback(cb_update_status)

        while not self.should_stop:
            cb_called.wait(2)

        self.failUnless(cb_called.isSet(), 'Answer callback was not triggered.')
        self.assertEqual(self.status['playlistlength'], 1)

    def testCallbackProcess(self):
        """ Send two commands asynchroneously at the same time and check callback """

        firstcb_called = threading.Event()
        secondcb_called = threading.Event()
        def first_cb(answer):
            firstcb_called.set()

        def second_cb(answer):
            secondcb_called.set()

        self.deejaydaemon.get_audio_dir("").add_callback(first_cb)
        self.deejaydaemon.get_playlist_list().add_callback(second_cb)
        
        secondcb_called.wait(2)
        firstcb_called.wait(2)
        self.failUnless(firstcb_called.isSet(), \
            '1rst Answer callback was not triggered.')
        self.failUnless(secondcb_called.isSet(), \
            '2nd Answer callback was not triggered.')
        
# vim: ts=4 sw=4 expandtab
