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
from deejayd.model.mediafilters import *

class SignalsInterfaceTests(_TestInterfaces):
    possible_clients = ("net_async",)

    def test_subscription(self):
        """Checks that signals subscriptions get in and out."""
        server_notification = threading.Event()

        sub_id = self.deejayd.subscribe('player.status',
                                        lambda x: server_notification.set())
        self.assertTrue((sub_id, 'player.status')\
                        in self.deejayd.get_subscriptions().items())

        self.deejayd.unsubscribe(sub_id)
        self.assertTrue((sub_id, 'player.status')\
                        not in self.deejayd.get_subscriptions().items())

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

        self.generic_sub_bcast_test('mode', client2.set_mode, ('video',))

    def test_sub_broadcast_player_status(self):
        """Checks that player.status signals are broadcasted."""
        self.deejayd.set_mode("playlist").wait_for_answer()
        djpl = self.deejayd.playlist
        ans = self.deejayd.audiolib.get_dir_content().wait_for_answer()
        d = self.testdata.getRandomElement(ans["directories"])
        djpl.add_path([d]).wait_for_answer()

        trigger_list = ((self.deejayd.player.play_toggle, ()),
                        (self.deejayd.set_option, ("playlist", 'repeat', True)),
                        (self.deejayd.set_option, ('panel', "playorder", \
                                                   "random")),
                        (self.deejayd.player.set_volume, (51,)),
                        (self.deejayd.player.seek, (5,)),
                       )

        for trig in trigger_list:
            self.generic_sub_bcast_test('player.status', trig[0], trig[1])

    def test_sub_broadcast_player_current(self):
        """Checks that player.current signals are broadcasted."""
        self.deejayd.set_mode("playlist").wait_for_answer()
        djpl = self.deejayd.playlist
        ans = self.deejayd.audiolib.get_dir_content().wait_for_answer()
        d = self.testdata.getRandomElement(ans["directories"])
        djpl.add_path([d]).wait_for_answer()
        self.deejayd.player.play_toggle().wait_for_answer()

        trigger_list = ((self.deejayd.player.next, ()),
                        (self.deejayd.player.previous, ())
                       )

        for trig in trigger_list:
            self.generic_sub_bcast_test('player.current', trig[0], trig[1])

    def test_sub_broadcast_player_plupdate(self):
        """Checks that player.plupdate signals are broadcasted."""

        djpl = self.deejayd.playlist
        ans = self.deejayd.audiolib.get_dir_content().wait_for_answer()
        dir = self.testdata.getRandomElement(ans["directories"])

        trigger_list = ((djpl.add_path, ([dir],)),
                        (djpl.shuffle, ()),
                        (djpl.clear, ()),
                       )

        for trig in trigger_list:
            self.generic_sub_bcast_test('player.plupdate', trig[0], trig[1])

    def test_sub_broadcast_playlist_listupdate(self):
        """Checks that playlist.listupdate signals are broadcasted."""

        djpl = self.deejayd.playlist
        ans = self.deejayd.audiolib.get_dir_content().wait_for_answer()
        dir = self.testdata.getRandomElement(ans["directories"])
        djpl.add_path([dir]).wait_for_answer()

        test_pl_name = self.testdata.getRandomString()
        test_pl_name2 = self.testdata.getRandomString()

        self.generic_sub_bcast_test('playlist.listupdate',
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
            self.generic_sub_bcast_test('playlist.listupdate', trig[0], trig[1])

    def test_sub_broadcast_playlist_update(self):
        """Checks that playlist.update signals are broadcasted."""
        ans = self.deejayd.audiolib.get_dir_content().wait_for_answer()
        dir = self.testdata.getRandomElement(ans["directories"])
        filter = Equals('genre', self.test_audiodata.getRandomGenre())

        st_pl_name = self.testdata.getRandomString()
        mg_pl_name = self.testdata.getRandomString()

        st_pl_id = self.deejayd.recpls.create(st_pl_name, \
                'static').wait_for_answer()["pl_id"]
        mg_pl_id = self.deejayd.recpls.create(mg_pl_name, \
                'magic').wait_for_answer()["pl_id"]

        recpls = self.deejayd.recpls
        trigger_list = (
                        (recpls.static_add_media, (st_pl_id, [dir],)),
                        (recpls.magic_add_filter, (mg_pl_id, filter,)),
                        (recpls.magic_remove_filter, (mg_pl_id, filter,)),
                        (recpls.magic_set_property, (mg_pl_id, 'use-limit', '1'))
                       )
        for trig in trigger_list:
            self.generic_sub_bcast_test('playlist.update', trig[0], trig[1])

    def test_sub_broadcast_panel_update(self):
        """Checks that panel.update signals are broadcasted."""

        # first save a playlist
        djpl = self.deejayd.playlist
        ans = self.deejayd.audiolib.get_dir_content().wait_for_answer()
        dir = self.testdata.getRandomElement(ans["directories"])
        djpl.add_path([dir]).wait_for_answer()
        test_pl_name = self.testdata.getRandomString()
        djpl.save(test_pl_name).wait_for_answer()
        pl_list = self.deejayd.recpls.get_list().wait_for_answer()
        if len(pl_list) != 1:
            raise DeejaydError("playlist not saved")

        djpn = self.deejayd.panel

        trigger_list = (
                        (djpn.set_active_list, ("playlist", pl_list[0]["pl_id"])),
                        (djpn.set_active_list, ("panel", "0")),
                        (djpn.set_filter, ("genre", ["zboub"])),
                        (djpn.clear_filters, []),
                        (djpn.set_sort, ([("genre", "ascending")],)),
                       )

        for trig in trigger_list:
            self.generic_sub_bcast_test('panel.update', trig[0], trig[1])

    @require_video_support
    def test_sub_broadcast_video_update(self):
        """Checks that video.update signals are broadcasted."""
        djvideo = self.deejayd.video
        ans = self.deejayd.videolib.get_dir_content().wait_for_answer()
        dir = self.testdata.getRandomElement(ans["directories"])

        trigger_list = (
                        (djvideo.set, (dir, "directory")),
                        (djvideo.set_sort, ([("title", "ascending")],)),
                       )

        for trig in trigger_list:
            self.generic_sub_bcast_test('video.update', trig[0], trig[1])

    def test_sub_broadcast_webradio_listupdate(self):
        """Checks that webradio.listupdate signals are broadcasted."""

        wr_list = self.deejayd.webradio
        test_wr_name = self.testdata.getRandomString()
        test_wr_urls = ['http://' + self.testdata.getRandomString(50)]

        self.generic_sub_bcast_test('webradio.listupdate',
                                    wr_list.source_add_webradio,
                                    ("local", test_wr_name, test_wr_urls))

        retrieved_wr = [wr for wr in wr_list.get().wait_for_answer()["medias"]\
                           if wr['title'] == test_wr_name][0]
        self.generic_sub_bcast_test('webradio.listupdate',
                                    wr_list.source_delete_webradios,
                                    ("local", [retrieved_wr['id']],))

    def test_sub_broadcast_queue_update(self):
        """Checks that queue.update signals are broadcasted."""

        q = self.deejayd.queue

        ans = self.deejayd.audiolib.get_dir_content().wait_for_answer()
        dir = self.testdata.getRandomElement(ans["directories"])

        self.generic_sub_bcast_test('queue.update', q.add_path, ([dir],))

        retrieved_song_id = [song['id'] \
                for song in q.get().wait_for_answer()["medias"]]
        self.generic_sub_bcast_test('queue.update',
                                    q.remove, (retrieved_song_id,))

    @require_video_support
    @unittest.skip("Dvd test not supported for now")
    def test_sub_broadcast_dvd_update(self):
        """Checks that dvd.update signals are broadcasted."""
        # disable test if video support or dvd mode are disabled
        self.generic_sub_bcast_test('dvd.update', self.deejayd.dvd.reload, ())

    def test_sub_broadcast_mode(self):
        """Checks that mode signals are broadcasted."""
        self.generic_sub_bcast_test('mode', self.deejayd.set_mode, ('webradio',))

    @unittest.skipIf(inotify is False, "inotify is not supported")
    def test_sub_broadcast_mediadb_aupdate(self):
        """Checks that mediadb.aupdate signals are broadcasted."""
        # This is tested only using inotify support
        self.generic_sub_bcast_test('mediadb.aupdate',
                                    self.test_audiodata.addMedia)

    @require_video_support
    @unittest.skipIf(inotify is False, "inotify is not supported")
    def test_sub_broadcast_mediadb_vupdate(self):
        """Checks that mediadb.vupdate signals are broadcasted."""
        # This is tested only using inotify support
        self.generic_sub_bcast_test('mediadb.vupdate',
                                    self.test_videodata.addMedia)
# vim: ts=4 sw=4 expandtab
