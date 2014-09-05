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
from deejayd import DeejaydError
from deejayd.mediadb import inotify
from testdeejayd import unittest
from testdeejayd.interfaces import require_video_support, _TestInterfaces
from deejayd.jsonrpc.mediafilters import *

class SignalsInterfaceTests(_TestInterfaces):
    possible_clients = ("net_async",)

    def test_subscription(self):
        """Checks that signals subscriptions get in and out."""
        server_notification = threading.Event()

        sub_id = self.deejayd.subscribe('player.status',
                                        lambda x: server_notification.set())
        self.assertTrue(self.deejayd.is_subscribed("player.status"))

        self.deejayd.unsubscribe(sub_id)
        self.assertFalse(self.deejayd.is_subscribed("player.status"))

    def generic_sub_bcast_test(self, signal_name, trigger, trigger_args=()):
        """Checks that signal_name signal is broadcast when one of the trigger is involved."""
        server_notification = threading.Event()

        sub_id = self.deejayd.subscribe(signal_name,
                                        lambda x: server_notification.set())

        ans = trigger(*trigger_args)
        if ans:
            ans.wait_for_answer()
        server_notification.wait(4)
        self.assertTrue(server_notification.isSet(),
                        '%s signal was not broadcasted by %s.'\
                        % (signal_name, trigger.__name__))
        server_notification.clear()

        self.deejayd.unsubscribe(sub_id)

    def test_subscription_another_client(self):
        """Checks that a subscription is broadcasted to another client who did not orignate the event trigger."""

        # Instanciate a second client that connects to the same server
        client2 = self.get_another_client()
        client2.connect('localhost', self.serverPort)

        self.generic_sub_bcast_test('player.status', client2.player.set_volume, ('40',))

    def test_sub_broadcast_player_status(self):
        """Checks that player.status signals are broadcasted."""
        djpl = self.deejayd.audiopls
        ans = self.deejayd.audiolib.get_dir_content().wait_for_answer()
        d = self.testdata.getRandomElement(ans["directories"])
        djpl.load_folders([d["id"]]).wait_for_answer()

        trigger_list = ((self.deejayd.player.play_toggle, ()),
                        (self.deejayd.player.set_volume, (51,)),
                        (self.deejayd.player.seek, (5,)),
                       )

        for trig in trigger_list:
            self.generic_sub_bcast_test('player.status', trig[0], trig[1])

    def test_sub_broadcast_player_current(self):
        """Checks that player.current signals are broadcasted."""
        djpl = self.deejayd.audiopls
        ans = self.deejayd.audiolib.get_dir_content().wait_for_answer()
        d = self.testdata.getRandomElement(ans["directories"])
        djpl.load_folders([d["id"]]).wait_for_answer()
        self.deejayd.player.play_toggle().wait_for_answer()

        trigger_list = ((self.deejayd.player.next, ()),
                        (self.deejayd.player.previous, ())
                       )

        for trig in trigger_list:
            self.generic_sub_bcast_test('player.current', trig[0], trig[1])

    def test_sub_broadcast_player_audioplsupdate(self):
        """Checks that audiopls.update signals are broadcasted."""

        djpl = self.deejayd.audiopls
        ans = self.deejayd.audiolib.get_dir_content().wait_for_answer()
        dir = self.testdata.getRandomElement(ans["directories"])

        trigger_list = ((djpl.load_folders, ([dir["id"]],)),
                        (djpl.shuffle, ()),
                        (djpl.set_option, ('repeat', True)),
                        (djpl.set_option, ("playorder", "random")),
                        (djpl.clear, ()),
                       )

        for trig in trigger_list:
            self.generic_sub_bcast_test('audiopls.update', trig[0], trig[1])

    def test_sub_broadcast_recpls_listupdate(self):
        """Checks that recpls.listupdate signals are broadcasted."""

        djpl = self.deejayd.audiopls
        ans = self.deejayd.audiolib.get_dir_content().wait_for_answer()
        dir = self.testdata.getRandomElement(ans["directories"])
        djpl.load_folders([dir["id"]]).wait_for_answer()

        test_pl_name = self.testdata.getRandomString()
        test_pl_name2 = self.testdata.getRandomString()

        self.generic_sub_bcast_test('recpls.listupdate',
                                    djpl.save, (test_pl_name,))

        retrievedPls = self.deejayd.recpls.get_list().wait_for_answer()
        for pls in retrievedPls:
            if pls["name"] == test_pl_name:
                djpl_id = pls["pl_id"]
                break
        trigger_list = (
                        (self.deejayd.recpls.erase, ([djpl_id],)),
                        (self.deejayd.recpls.create, (test_pl_name, "static")),
                        (djpl.save, (test_pl_name2,)),
                       )

        for trig in trigger_list:
            self.generic_sub_bcast_test('recpls.listupdate', trig[0], trig[1])

    def test_sub_broadcast_recpls_update(self):
        """Checks that recpls.update signals are broadcasted."""
        ans = self.deejayd.audiolib.get_dir_content().wait_for_answer()
        dir = self.testdata.getRandomElement(ans["directories"])
        filter = Equals('genre', self.test_audiodata.getRandomGenre())

        st_pl_name = self.testdata.getRandomString()
        mg_pl_name = self.testdata.getRandomString()

        recpls = self.deejayd.recpls
        st_pl_id = recpls.create(st_pl_name, \
                'static').wait_for_answer()["pl_id"]
        mg_pl_id = recpls.create(mg_pl_name, \
                'magic').wait_for_answer()["pl_id"]

        trigger_list = (
                        (recpls.static_load_folders, (st_pl_id, [dir["id"]],)),
                        (recpls.magic_add_filter, (mg_pl_id, filter,)),
                        (recpls.magic_remove_filter, (mg_pl_id, filter,)),
                        (recpls.magic_set_property, (mg_pl_id, 'use-limit', '1'))
                       )
        for trig in trigger_list:
            self.generic_sub_bcast_test('recpls.update', trig[0], trig[1])

    def test_sub_broadcast_audioqueue_update(self):
        """Checks that audioqueue.update signals are broadcasted."""

        q = self.deejayd.audioqueue

        ans = self.deejayd.audiolib.get_dir_content().wait_for_answer()
        dir = self.testdata.getRandomElement(ans["directories"])

        self.generic_sub_bcast_test('audioqueue.update', \
                                    q.load_folders, ([dir["id"]],))

        retrieved_song_id = [song['id'] \
                             for song in q.get().wait_for_answer()]
        self.generic_sub_bcast_test('audioqueue.update',
                                    q.remove, (retrieved_song_id,))

    @require_video_support
    def test_sub_broadcast_videopls_update(self):
        """Checks that videopls.update signals are broadcasted."""
        djvideo = self.deejayd.videopls
        ans = self.deejayd.videolib.get_dir_content().wait_for_answer()
        dir = self.testdata.getRandomElement(ans["directories"])

        trigger_list = ((djvideo.load_folders, ([dir["id"]],)),
                        (djvideo.shuffle, ()),
                        (djvideo.set_option, ('repeat', True)),
                        (djvideo.set_option, ("playorder", "random")),
                        (djvideo.clear, ()),
        )

        for trig in trigger_list:
            self.generic_sub_bcast_test('videopls.update', trig[0], trig[1])

    def test_sub_broadcast_webradio_listupdate(self):
        """Checks that webradio.listupdate signals are broadcasted."""

        wr_list = self.deejayd.webradio
        test_wr_name = self.testdata.getRandomString()
        test_wr_urls = ['http://' + self.testdata.getRandomString(50)]

        self.generic_sub_bcast_test('webradio.listupdate',
                                    wr_list.source_add_webradio,
                                    ("local", test_wr_name, test_wr_urls))

        retrieved_wr = [wr for wr in wr_list.get_source_content("local").wait_for_answer()\
                           if wr['title'] == test_wr_name][0]
        self.generic_sub_bcast_test('webradio.listupdate',
                                    wr_list.source_delete_webradios,
                                    ("local", [retrieved_wr['wb_id']],))

    def test_sub_broadcast_mediadb_aupdate(self):
        """Checks that mediadb.aupdate signals are broadcasted."""
        self.generic_sub_bcast_test('mediadb.aupdate',
                                    self.deejayd.audiolib.update)

    @require_video_support
    def test_sub_broadcast_mediadb_vupdate(self):
        """Checks that mediadb.vupdate signals are broadcasted."""
        self.generic_sub_bcast_test('mediadb.vupdate',
                                    self.deejayd.videolib.update)
# vim: ts=4 sw=4 expandtab
