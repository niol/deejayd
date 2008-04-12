# Deejayd, a media player daemon
# Copyright (C) 2007-2008 Mickael Royer <mickael.royer@gmail.com>
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


import time, random
import threading

from deejayd.interfaces import DeejaydError


class InterfaceTests:
    """Test the deejayd daemon core interface, this test suite is to be used for testing the core facade and the client library."""

    def testSetMode(self):
        """Test setMode command"""

        # ask an unknown mode
        mode_name = self.testdata.getRandomString()
        ans = self.deejayd.set_mode(mode_name)
        self.assertRaises(DeejaydError, ans.get_contents)

        # ask a known mode
        known_mode = 'playlist'
        ans = self.deejayd.set_mode(known_mode)
        self.failUnless(ans.get_contents())

        # Test if the mode has been set
        status = self.deejayd.get_status().get_contents()
        self.assertEqual(status['mode'], known_mode)

    def testGetMode(self):
        """Test getMode command"""
        known_keys = ("playlist","dvd","webradio","video")
        ans = self.deejayd.get_mode()
        for k in known_keys:
            self.failUnless(k in ans.get_contents().keys())
            self.failUnless(int(ans[k]) in (0,1))

    def testGetStats(self):
        """Test getStats command"""
        ans = self.deejayd.get_stats()
        for k in ("audio_library_update","songs","artists","albums"):
            self.failUnless(k in ans.keys())

    def testPlaylistSaveRetrieve(self):
        """Save a playlist and try to retrieve it."""

        pl = []
        djplname = self.testdata.getRandomString()

        # Get current playlist
        djpl = self.deejayd.get_playlist()
        self.assertEqual(djpl.get().get_medias(), pl)

        ans = djpl.add_song(self.testdata.getRandomString())
        self.assertRaises(DeejaydError, ans.get_contents)

        # Add songs to playlist
        howManySongs = 3
        for songPath in self.test_audiodata.getRandomSongPaths(howManySongs):
            pl.append(songPath)
            ans = djpl.add_song(songPath)
            self.failUnless(ans.get_contents())

        # Check for the playlist to be of appropriate length
        self.assertEqual(self.deejayd.get_status()['playlistlength'],
                         howManySongs)

        ans = djpl.save(djplname)
        self.failUnless(ans.get_contents())

        # Check for the saved playslit to be available
        retrievedPls = self.deejayd.get_playlist_list().get_medias()
        self.failUnless(djplname in [p["name"] for p in retrievedPls])

        # Retrieve the saved playlist
        djpl = self.deejayd.get_playlist(djplname)
        retrievedPl = djpl.get().get_medias()
        for song_nb in range(len(pl)):
            self.assertEqual(pl[song_nb], retrievedPl[song_nb]['path'])

    def testWebradioAddRetrieve(self):
        """Save a webradio and check it is in the list, then delete it."""

        wr_list = self.deejayd.get_webradios()

        # Test for bad URI and inexistant playlist
        for badURI in [[self.testdata.getRandomString(50)],]:
                   #['http://' + self.testdata.getRandomString(50) + '.pls']]:
            ans = wr_list.add_webradio(self.testdata.getRandomString(),
                                       badURI[0])
            # FIXME : provision for the future where the same webradio may have
            # multiple urls.
            #                          badURI)
            self.assertRaises(DeejaydError, ans.get_contents)

        testWrName = self.testdata.getRandomString()

        # FIXME : provision for the future where the same webradio may have
        # multiple urls.
        # testWrUrls = []
        # for urlCount in range(self.testdata.getRandomInt(10)):
        #     testWrUrls.append('http://' + self.testdata.getRandomString(50))
        testWrUrls = 'http://' + self.testdata.getRandomString(50)

        ans = wr_list.add_webradio(testWrName, testWrUrls)
        self.failUnless(ans.get_contents())

        # FIXME : This should not be, see the future of webradios.
        testWrName += '-1'

        wr_list = self.deejayd.get_webradios()
        wr_names = [wr['title'] for wr in wr_list.get().get_medias()]
        self.failUnless(testWrName in wr_names)

        retrievedWr = [wr for wr in wr_list.get().get_medias()\
                          if wr['title'] == testWrName][0]

        # FIXME : Same provision for the future.
        # for url in testWrUrls:
        #     self.failUnless(url in retrievedWr['Url'])
        self.assertEqual(testWrUrls, retrievedWr['url'])

        ans = wr_list.delete_webradio(51)
        self.assertRaises(DeejaydError, ans.get_contents)

        ans = wr_list.delete_webradio(retrievedWr['id'])
        self.failUnless(ans.get_contents())

        wr_list = self.deejayd.get_webradios().get().get_medias()
        self.failIf(testWrName in [wr['title'] for wr in wr_list])

    def testQueue(self):
        """Add songs to the queue, try to retrieve it, delete some songs in it, then clear it."""
        q = self.deejayd.get_queue()

        myq = []
        how_many_songs = 10
        for song_path in self.test_audiodata.getRandomSongPaths(how_many_songs):
            myq.append(song_path)
            ans = q.add_media(song_path)
            self.failUnless(ans.get_contents())

        ddq = q.get()

        ddq_paths = [song['path'] for song in ddq.get_medias()]
        for song_path in myq:
            self.failUnless(song_path in ddq_paths)

        random.seed(time.time())
        songs_to_delete = random.sample(myq, how_many_songs / 3)
        ans = q.del_songs([song['id'] for song in ddq.get_medias()\
                                      if song['path'] in songs_to_delete])
        self.failUnless(ans.get_contents())

        ddq = q.get()
        ddq_paths = [song['path'] for song in ddq.get_medias()]
        for song_path in myq:
            if song_path in songs_to_delete:
                self.failIf(song_path in ddq_paths)
            else:
                self.failUnless(song_path in ddq_paths)

        ans = q.clear()
        self.failUnless(ans.get_contents())
        ddq = q.get()
        self.assertEqual(ddq.get_medias(), [])

    def testVideo(self):
        """ Test video source actions """
        video_obj = self.deejayd.get_video()
        # choose a wrong directory
        rand_dir = self.testdata.getRandomString()
        ans = video_obj.set(rand_dir, "directory")
        self.assertRaises(DeejaydError, ans.get_contents)

        # get contents of root dir and try to set video directory
        ans = self.deejayd.get_video_dir()
        dir = self.testdata.getRandomElement(ans.get_directories())
        video_obj.set(dir, "directory").get_contents()

        # test videolist content
        video_list = video_obj.get().get_medias()
        self.assertEqual(len(video_list), len(ans.get_files()))

        # search a wrong title
        rand = self.testdata.getRandomString()
        video_obj.set(rand, "search").get_contents()
        video_list = video_obj.get().get_medias()
        self.assertEqual(len(video_list), 0)


    def testAudioLibrary(self):
        """ Test request on audio library (get_audio_dir, search)"""
        # try to get contents of an unknown directory
        rand_dir = self.testdata.getRandomString()
        ans = self.deejayd.get_audio_dir(rand_dir)
        self.assertRaises(DeejaydError, ans.get_contents)

        # get contents of root dir and try to get content of a directory
        ans = self.deejayd.get_audio_dir()
        dir = self.testdata.getRandomElement(ans.get_directories())
        ans = self.deejayd.get_audio_dir(dir)
        song_files = ans.get_files()
        self.failUnless(len(song_files) > 0)

        # search an unknown terms
        text = self.testdata.getRandomString()
        ans = self.deejayd.audio_search(text)
        self.assertEqual(ans.get_files(), [])

        # search a known terms
        file = self.testdata.getRandomElement(song_files)
        ans = self.deejayd.audio_search(file["title"])
        self.failUnless(len(ans.get_files()) > 0)

    def testVideoLibrary(self):
        """ Test request on video library """
        # try to get contents of an unknown directory
        rand_dir = self.testdata.getRandomString()
        ans = self.deejayd.get_video_dir(rand_dir)
        self.assertRaises(DeejaydError, ans.get_contents)

        # get contents of root dir and try to get content of a directory
        ans = self.deejayd.get_video_dir()
        dir = self.testdata.getRandomElement(ans.get_directories())
        ans = self.deejayd.get_video_dir(dir)
        files = ans.get_files()
        self.failUnless(len(files) > 0)

    def testSetOption(self):
        """ Test set_option commands"""
        # unknown option
        opt = self.testdata.getRandomString()
        ans = self.deejayd.set_option(opt, 1)
        self.assertRaises(DeejaydError, ans.get_contents)

        # known option
        opt = self.testdata.getRandomElement(('random','repeat'))
        ans = self.deejayd.set_option(opt, 1).get_contents()
        status = self.deejayd.get_status().get_contents()
        self.assertEqual(status[opt], 1)

    def testAudioPlayer(self):
        """ Test player commands (play, pause,...) for audio """
        # try to set volume
        vol = 30
        ans = self.deejayd.set_volume(vol)
        self.failUnless(ans.get_contents())
        status = self.deejayd.get_status().get_contents()
        self.assertEqual(status["volume"], vol)

        # load songs in main playlist
        djpl = self.deejayd.get_playlist()
        ans = self.deejayd.get_audio_dir()
        dir = self.testdata.getRandomElement(ans.get_directories())
        djpl.add_songs([dir]).get_contents()

        # play song
        self.deejayd.set_mode("playlist").get_contents()
        self.deejayd.play_toggle().get_contents()
        # verify status
        status = self.deejayd.get_status().get_contents()
        self.assertEqual(status["state"], "play")
        # pause
        self.deejayd.play_toggle().get_contents()
        # verify status
        status = self.deejayd.get_status().get_contents()
        self.assertEqual(status["state"], "pause")
        self.deejayd.play_toggle().get_contents()
        # next and previous
        self.deejayd.next().get_contents()
        self.deejayd.previous().get_contents()
        status = self.deejayd.get_status().get_contents()
        self.assertEqual(status["state"], "play")
        # seek command
        self.deejayd.seek(1).get_contents()

        # test get_current command
        cur = self.deejayd.get_current().get_medias()
        self.assertEqual(len(cur), 1)

        self.deejayd.stop().get_contents()

    def testVideoPlayer(self):
        """ Test player commands (play, pause,...) for video """
        video_obj = self.deejayd.get_video()
        # set video mode
        self.deejayd.set_mode("video").get_contents()

        # choose directory
        ans = self.deejayd.get_video_dir()
        dir = self.testdata.getRandomElement(ans.get_directories())
        video_obj.set(dir, "directory").get_contents()

        # play video file
        self.deejayd.play_toggle().get_contents()
        # verify status
        status = self.deejayd.get_status().get_contents()
        self.assertEqual(status["state"], "play")
        # test set_player_option cmd
        self.deejayd.set_player_option("av_offset", 100)

        self.deejayd.stop().get_contents()

    def testDvd(self):
        """ Test dvd commands"""
        status = self.deejayd.get_status().get_contents()
        dvd_id = status["dvd"]

        self.deejayd.dvd_reload().get_contents()
        status = self.deejayd.get_status().get_contents()
        self.assertEqual(status["dvd"], dvd_id + 1)


class InterfaceSubscribeTests:
    """Test the subscription interface. This is for the core and the async client only."""

    def test_subscription(self):
        """Checks that signals subscriptions get in and out."""
        server_notification = threading.Event()

        self.assertEqual(self.deejayd.get_subscriptions(), {})

        sub_id = self.deejayd.subscribe('player.status',
                                        lambda x: server_notification.set())
        self.failUnless((sub_id, 'player.status')\
                        in self.deejayd.get_subscriptions().items())

        self.deejayd.unsubscribe(sub_id)
        self.assertEqual(self.deejayd.get_subscriptions(), {})

    def generic_sub_bcast_test(self, signal_name, trigger, trigger_args=()):
        """Checks that signal_name signal is broadcast when one of the trigger is involved."""
        server_notification = threading.Event()

        sub_id = self.deejayd.subscribe(signal_name,
                                        lambda x: server_notification.set())

        ans = trigger(*trigger_args)
        if ans:
            ans.get_contents()
        server_notification.wait(4)
        self.failUnless(server_notification.isSet(),
                        '%s signal was not broadcasted by %s.'\
                        % (signal_name, trigger.__name__))
        server_notification.clear()

        self.deejayd.unsubscribe(sub_id)

    def test_sub_broadcast_player_status(self):
        """Checks that player.status signals are broadcasted."""

        trigger_list = ((self.deejayd.play_toggle, ()),
                        (self.deejayd.set_option, ('random', 1)),
                        (self.deejayd.set_option, ('repeat', 1)),
                        (self.deejayd.set_volume, (51, )),
                        (self.deejayd.seek, (5, )),
                       )

        for trig in trigger_list:
            self.generic_sub_bcast_test('player.status', trig[0], trig[1])

    def test_sub_broadcast_player_current(self):
        """Checks that player.current signals are broadcasted."""

        trigger_list = ((self.deejayd.next, ()),
                        (self.deejayd.previous, ())
                       )

        for trig in trigger_list:
            self.generic_sub_bcast_test('player.current', trig[0], trig[1])

    def test_sub_broadcast_player_plupdate(self):
        """Checks that player.plupdate signals are broadcasted."""

        djpl = self.deejayd.get_playlist()
        ans = self.deejayd.get_audio_dir()
        dir = self.testdata.getRandomElement(ans.get_directories())

        trigger_list = ((djpl.add_songs, ([dir], )),
                        (djpl.shuffle, ()),
                        (djpl.clear, ()),
                       )

        for trig in trigger_list:
            self.generic_sub_bcast_test('player.plupdate', trig[0], trig[1])

    def test_sub_broadcast_playlist_update(self):
        """Checks that playlist.update signals are broadcasted."""

        djpl = self.deejayd.get_playlist()
        ans = self.deejayd.get_audio_dir()
        dir = self.testdata.getRandomElement(ans.get_directories())
        djpl.add_songs([dir]).get_contents()

        test_pl_name = self.testdata.getRandomString()

        self.generic_sub_bcast_test('playlist.update',
                                    djpl.save, (test_pl_name, ))

        saved_djpl = self.deejayd.get_playlist(test_pl_name)

        trigger_list = ((saved_djpl.shuffle, ()),
                        (saved_djpl.clear, ()),
                        (self.deejayd.erase_playlist, ([test_pl_name], )),
                       )

        for trig in trigger_list:
            self.generic_sub_bcast_test('playlist.update', trig[0], trig[1])

    def test_sub_broadcast_webradio_listupdate(self):
        """Checks that webradio.listupdate signals are broadcasted."""

        wr_list = self.deejayd.get_webradios()
        test_wr_name = self.testdata.getRandomString()
        test_wr_urls = 'http://' + self.testdata.getRandomString(50)

        self.generic_sub_bcast_test('webradio.listupdate',
                                    wr_list.add_webradio,
                                    (test_wr_name, test_wr_urls))

        retrieved_wr = [wr for wr in wr_list.get().get_medias()\
                           if wr['title'] == test_wr_name + '-1'][0]
        self.generic_sub_bcast_test('webradio.listupdate',
                                    wr_list.delete_webradio,
                                    (retrieved_wr['id'], ))

    def test_sub_broadcast_queue_update(self):
        """Checks that queue.update signals are broadcasted."""

        q = self.deejayd.get_queue()

        ans = self.deejayd.get_audio_dir()
        dir = self.testdata.getRandomElement(ans.get_directories())

        self.generic_sub_bcast_test('queue.update', q.add_medias, ([dir], ))

        retrieved_song_id = [song['id'] for song in q.get().get_medias()]
        self.generic_sub_bcast_test('queue.update',
                                    q.del_songs, (retrieved_song_id, ))

    def test_sub_broadcast_dvd_update(self):
        """Checks that dvd.update signals are broadcasted."""
        self.generic_sub_bcast_test('dvd.update', self.deejayd.dvd_reload, ())

    def test_sub_broadcast_mode(self):
        """Checks that mode signals are broadcasted."""
        self.generic_sub_bcast_test('mode', self.deejayd.set_mode, ('video', ))

    def test_sub_broadcast_mediadb_aupdate(self):
        """Checks that mediadb.aupdate signals are broadcasted."""

        # This is tested only using inotify support
        self.generic_sub_bcast_test('mediadb.aupdate',
                                    self.test_audiodata.addMedia)

    def test_sub_broadcast_mediadb_vupdate(self):
        """Checks that mediadb.vupdate signals are broadcasted."""
        # This is tested only using inotify support
        self.generic_sub_bcast_test('mediadb.vupdate',
                                    self.test_videodata.addMedia)


# vim: ts=4 sw=4 expandtab
