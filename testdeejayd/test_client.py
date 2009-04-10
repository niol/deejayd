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

"""Deejayd Client library testing"""
import threading

from testdeejayd import TestCaseWithAudioAndVideoData

from testdeejayd.server import TestServer
from testdeejayd.coreinterface import InterfaceTests, InterfaceSubscribeTests
from deejayd.net.client import DeejayDaemonSync, DeejayDaemonAsync, \
                               DeejaydError, DeejaydWebradioList


class TestSyncClient(TestCaseWithAudioAndVideoData, InterfaceTests):
    """Test the DeejaydClient library in synchroneous mode."""

    def setUp(self):
        TestCaseWithAudioAndVideoData.setUp(self)

        # Set up the test server
        testServerPort = 23344
        dbfilename = '/tmp/testdeejayddb-' +\
                     self.testdata.getRandomString() + '.db'
        self.testserver = TestServer(testServerPort,
            self.test_audiodata.getRootDir(), self.test_videodata.getRootDir(),
            dbfilename)
        self.testserver.start()

        # Instanciate the server object of the client library
        self.deejayd = DeejayDaemonSync()
        self.deejayd.connect('localhost', testServerPort)

    def tearDown(self):
        self.deejayd.disconnect()
        self.testserver.stop()
        TestCaseWithAudioAndVideoData.tearDown(self)

    def testPing(self):
        """Ping server"""
        self.failUnless(self.deejayd.ping().get_contents())


class TestAsyncClient(TestCaseWithAudioAndVideoData, InterfaceSubscribeTests):
    """Test the DeejaydClient library in asynchroenous mode."""

    def setUp(self):
        TestCaseWithAudioAndVideoData.setUp(self)

        # Set up the test server
        self.testServerPort = 23344
        dbfilename = '/tmp/testdeejayddb-' +\
                     self.testdata.getRandomString() + '.db'
        self.testserver = TestServer(self.testServerPort,
            self.test_audiodata.getRootDir(), self.test_videodata.getRootDir(),
            dbfilename)
        self.testserver.start()

        # Instanciate the server object of the client library
        self.deejayd = DeejayDaemonAsync()
        self.deejayd.connect('localhost', self.testServerPort)

        # Prepare in case we need other clients
        self.clients = [self.deejayd]

    def tearDown(self):
        for client in self.clients:
            client.disconnect()

        self.testserver.stop()
        TestCaseWithAudioAndVideoData.tearDown(self)

    def get_another_client(self):
        client = DeejayDaemonAsync()
        self.clients.append(client)
        return client

    def test_ping(self):
        """Ping server asynchroneously"""
        ans = self.deejayd.ping()
        self.failUnless(ans.get_contents(),
                        'Server did not respond well to ping.')

    def test_answer_callback(self):
        """Ping server asynchroneously and check for the callback to be triggered"""
        cb_called = threading.Event()
        def tcb(answer):
            cb_called.set()

        ans = self.deejayd.ping()
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

        djpl = self.deejayd.get_playlist()
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
            self.deejayd.get_status().add_callback(tcb_status)

        djpl.add_path(self.test_audiodata.getRandomSongPaths(1)[0]).\
                add_callback(cb_update_status)

        while not self.should_stop:
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

        self.deejayd.get_audio_dir("").add_callback(first_cb)
        self.deejayd.get_playlist_list().add_callback(second_cb)
        self.deejayd.ping().add_callback(third_cb)

        firstcb_called.wait(2)
        self.failUnless(firstcb_called.isSet(), \
            '1st Answer callback was not triggered.')
        secondcb_called.wait(2)
        self.failUnless(secondcb_called.isSet(), \
            '2nd Answer callback was not triggered.')
        thirdcb_called.wait(2)
        self.failUnless(thirdcb_called.isSet(), \
            '3rd Answer callback was not triggered.')

    def test_two_clients(self):
        """Checks that it is possible to instanciate two clients in the same process."""
        client2 = self.get_another_client()
        client2.connect('localhost', self.testServerPort)

        self.failUnless(self.deejayd.ping().get_contents())
        self.failUnless(client2.ping().get_contents())

    def test_subscription_another_client(self):
        """Checks that a subscription is broadcasted to another client who did not orignate the event trigger."""

        # Instanciate a second client that connects to the same server
        client2 = self.get_another_client()
        client2.connect('localhost', self.testServerPort)

        self.generic_sub_bcast_test('mode', client2.set_mode, ('video', ))


# vim: ts=4 sw=4 expandtab
