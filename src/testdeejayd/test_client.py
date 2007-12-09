"""Deejayd Client library testing"""
import threading

from testdeejayd import TestCaseWithMediaData

from testdeejayd.server import TestServer
from testdeejayd.coreinterface import InterfaceTests
from deejayd.net.client import DeejayDaemonSync, DeejayDaemonAsync, \
                               DeejaydError, DeejaydPlaylist,\
                               DeejaydWebradioList


class TestSyncClient(TestCaseWithMediaData, InterfaceTests):
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
        self.deejayd = DeejayDaemonSync()
        self.deejayd.connect('localhost', testServerPort)

    def tearDown(self):
        self.deejayd.disconnect()
        self.testserver.stop()
        TestCaseWithMediaData.tearDown(self)

    def testPing(self):
        """Ping server"""
        self.failUnless(self.deejayd.ping().get_contents())


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

        cb_called.wait(4)

        self.failUnless(cb_called.isSet(), 'Answer callback was not triggered.')
        self.assertEqual(self.status['playlistlength'], 1)

    def testCallbackProcess(self):
        """ Send three commands asynchroneously at the same time and check callback """

        firstcb_called = threading.Event()
        secondcb_called = threading.Event()
        thirdcb_called = threading.Event()
        def first_cb(answer):
            firstcb_called.set()

        def second_cb(answer):
            secondcb_called.set()

        def third_cb(answer):
            thirdcb_called.set()

        self.deejaydaemon.get_audio_dir("").add_callback(first_cb)
        self.deejaydaemon.get_playlist_list().add_callback(second_cb)
        self.deejaydaemon.ping().add_callback(third_cb)

        firstcb_called.wait(2)
        self.failUnless(firstcb_called.isSet(), \
            '1rst Answer callback was not triggered.')
        secondcb_called.wait(2)
        self.failUnless(secondcb_called.isSet(), \
            '2nd Answer callback was not triggered.')
        thirdcb_called.wait(2)
        self.failUnless(thirdcb_called.isSet(), \
            '3rd Answer callback was not triggered.')

# vim: ts=4 sw=4 expandtab
