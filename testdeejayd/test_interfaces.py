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

import threading

from testdeejayd import TestCaseWithServer, TestCaseWithDeejaydCore
from deejayd.net.client import DeejayDaemonSync, DeejayDaemonAsync, \
                               DeejayDaemonHTTP

from testdeejayd.interfaces.core import CoreInterfaceTests
from testdeejayd.interfaces.library import LibraryInterfaceTests
from testdeejayd.interfaces.player import PlayerInterfaceTests
from testdeejayd.interfaces.queue import QueueInterfaceTests
from testdeejayd.interfaces.playlist import PlaylistInterfaceTests
from testdeejayd.interfaces.recorded_playlist import RecordedPlaylistInterfaceTests
from testdeejayd.interfaces.video import VideoInterfaceTests
from testdeejayd.interfaces.panel import PanelInterfaceTests
from testdeejayd.interfaces.webradio import WebradioInterfaceTests
from testdeejayd.interfaces.signals import SignalsInterfaceTests


class TestCore(TestCaseWithDeejaydCore, CoreInterfaceTests, \
               LibraryInterfaceTests, PlayerInterfaceTests,\
               QueueInterfaceTests, PlaylistInterfaceTests,\
               RecordedPlaylistInterfaceTests, VideoInterfaceTests,\
               PanelInterfaceTests, WebradioInterfaceTests):
    """Test the deejayd daemon core."""

    def tearDown(self):
        self.deejayd.player.stop()
        self.deejayd.queue.clear()
        self.deejayd.playlist.clear()
        self.deejayd.panel.set_active_list("panel")
        self.deejayd.panel.clear_all_filters()
        # remove recorded playlist
        pl_list = self.deejayd.recpls.get_list()
        self.deejayd.recpls.erase([pl["pl_id"] for pl in pl_list])
        # remove recorded webradio
        self.deejayd.webradio.source_clear_webradios("local")              
          
    def assertAckCmd(self, cmd_res):
        self.assertEqual(cmd_res, None)      


class TestHTTPClient(TestCaseWithServer, CoreInterfaceTests):
    """Test the http client library"""

    def assertAckCmd(self, cmd_res):
        self.assertEqual(cmd_res, True)
        
    @classmethod
    def setUpClass(cls):
        super(TestHTTPClient, cls).setUpClass()

        url = cls.config.get("webui", "root_url")
        cls.deejayd = DeejayDaemonHTTP('localhost', cls.webServerPort, url)


class TestSyncClient(TestCaseWithServer, CoreInterfaceTests, \
               LibraryInterfaceTests, PlayerInterfaceTests,\
               QueueInterfaceTests, PlaylistInterfaceTests,\
               RecordedPlaylistInterfaceTests, VideoInterfaceTests,\
               PanelInterfaceTests, WebradioInterfaceTests):
    """Test the DeejaydClient library in synchronous mode."""

    def assertAckCmd(self, cmd_res):
        self.assertEqual(cmd_res, True)

    @classmethod
    def setUpClass(cls):
        super(TestSyncClient, cls).setUpClass()
        # Instanciate the server object of the client library
        cls.deejayd = DeejayDaemonSync()
        cls.deejayd.connect('localhost', cls.serverPort)

    @classmethod
    def tearDownClass(cls):
        cls.deejayd.disconnect()
        super(TestSyncClient, cls).tearDownClass()
    
    def tearDown(self):
        self.deejayd.player.stop()
        self.deejayd.queue.clear()
        self.deejayd.playlist.clear()
        self.deejayd.panel.set_active_list("panel")
        self.deejayd.panel.clear_all_filters()
        # remove recorded playlist
        pl_list = self.deejayd.recpls.get_list()
        self.deejayd.recpls.erase([pl["pl_id"] for pl in pl_list])
        # remove recorded webradio
        self.deejayd.webradio.source_clear_webradios("local")


class TestAsyncClient(TestCaseWithServer, SignalsInterfaceTests):
    """Test the DeejaydClient library in asynchronous mode."""

    @classmethod
    def setUpClass(cls):
        super(TestAsyncClient, cls).setUpClass()
        # Instanciate the server object of the client library
        cls.deejayd = DeejayDaemonAsync()
        cls.deejayd.connect('localhost', cls.serverPort)
        
        # Prepare in case we need other clients
        cls.clients = [cls.deejayd]

    @classmethod
    def tearDownClass(cls):
        for client in cls.clients:
            client.disconnect()
        super(TestAsyncClient, cls).tearDownClass()
    
    def tearDown(self):
        self.deejayd.player.stop().wait_for_answer()
        self.deejayd.queue.clear().wait_for_answer()
        self.deejayd.playlist.clear().wait_for_answer()
        self.deejayd.panel.set_active_list("panel").wait_for_answer()
        self.deejayd.panel.clear_all_filters().wait_for_answer()
        # remove recorded playlist
        pl_list = self.deejayd.recpls.get_list().wait_for_answer()
        self.deejayd.recpls.erase([pl["pl_id"] for pl in pl_list]).wait_for_answer()
        # remove recorded webradio
        self.deejayd.webradio.source_clear_webradios("local").wait_for_answer()

    def get_another_client(self):
        client = DeejayDaemonAsync()
        self.clients.append(client)
        return client

    def test_answer_callback(self):
        """Ping server asynchroneously and check for the callback to be triggered"""
        cb_called = threading.Event()
        def tcb(answer):
            cb_called.set()

        ans = self.deejayd.ping()
        ans.add_callback(tcb)
        # some seconds should be enough for the callback to be called
        cb_called.wait(4)
        self.assertTrue(cb_called.isSet(), 'Answer callback was not triggered.')

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

        self.deejayd.audiolib.get_dir_content().add_callback(first_cb)
        self.deejayd.recpls.get_list().add_callback(second_cb)
        self.deejayd.ping().add_callback(third_cb)

        firstcb_called.wait(2)
        self.assertTrue(firstcb_called.isSet(), \
            '1st Answer callback was not triggered.')
        secondcb_called.wait(2)
        self.assertTrue(secondcb_called.isSet(), \
            '2nd Answer callback was not triggered.')
        thirdcb_called.wait(2)
        self.assertTrue(thirdcb_called.isSet(), \
            '3rd Answer callback was not triggered.')

    def test_two_clients(self):
        """Checks that it is possible to instanciate two clients in the same process."""
        client2 = self.get_another_client()
        client2.connect('localhost', self.serverPort)

        self.assertTrue(self.deejayd.ping().wait_for_answer())
        self.assertTrue(client2.ping().wait_for_answer())

# vim: ts=4 sw=4 expandtab
