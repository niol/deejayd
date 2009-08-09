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


import time, random
import threading

from deejayd.interfaces import DeejaydError
from deejayd.mediafilters import *


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

        ans = djpl.add_path(self.testdata.getRandomString())
        self.assertRaises(DeejaydError, ans.get_contents)

        # Add songs to playlist
        howManySongs = 3
        for songPath in self.test_audiodata.getRandomSongPaths(howManySongs):
            pl.append(self.test_audiodata.medias[songPath].tags["uri"])
            ans = djpl.add_path(songPath)
            self.failUnless(ans.get_contents())

        # Check for the playlist to be of appropriate length
        self.assertEqual(self.deejayd.get_status()['playlistlength'],
                         howManySongs)

        ans = djpl.save(djplname)

        self.failUnless(ans.get_contents())
        djpl_id = ans["playlist_id"]

        # Check for the saved playslit to be available
        retrievedPls = self.deejayd.get_playlist_list().get_medias()
        self.failUnless(djplname in [p["name"] for p in retrievedPls])

        # Retrieve the saved playlist
        djpl = self.deejayd.get_recorded_playlist(djpl_id, djplname, 'static')
        retrievedPl = djpl.get().get_medias()
        for song_nb in range(len(pl)):
            self.assertEqual(pl[song_nb], retrievedPl[song_nb]['uri'])

    def testPlaylistActions(self):
        """Test actions on current playlist."""
        djpl = self.deejayd.get_playlist()
        howManySongs = 4
        for songPath in self.test_audiodata.getRandomSongPaths(howManySongs):
            ans = djpl.add_path(songPath)
            self.failUnless(ans.get_contents())

        content = djpl.get().get_medias()
        song = self.testdata.getRandomElement(content)
        # shuffle the playlist
        ans = djpl.shuffle()
        self.failUnless(ans.get_contents())
        # move this song
        ans = djpl.move([song["id"]], 1)
        self.failUnless(ans.get_contents())
        # delete a song
        djpl.del_song(song["id"]).get_contents()
        content = djpl.get().get_medias()
        self.assertEqual(len(content), howManySongs-1)

    def testSavedStaticPlaylistActions(self):
        """Test action on saved static playlist"""
        djplname = self.testdata.getRandomString()
        djpl = self.deejayd.get_playlist()
        howManySongs = 3
        # Add songs to playlist
        for songPath in self.test_audiodata.getRandomSongPaths(howManySongs):
            ans = djpl.add_path(songPath)
            self.failUnless(ans.get_contents())
        # save playlist
        ans = djpl.save(djplname)
        self.failUnless(ans.get_contents())
        djpl_id = ans["playlist_id"]

        # add songs in the saved playlist
        savedpl = self.deejayd.get_recorded_playlist(djpl_id, djplname,\
                "static")
        for songPath in self.test_audiodata.getRandomSongPaths(howManySongs):
            # add twice the same song
            ans = savedpl.add_path(songPath)
            self.failUnless(ans.get_contents())
            ans = savedpl.add_path(songPath)
            self.failUnless(ans.get_contents())
        content = savedpl.get().get_medias()
        self.assertEqual(len(content), howManySongs*3)

    def testSavedMagicPlaylistActions(self):
        """Test action on saved magic playlist"""
        djplname = self.testdata.getRandomString()
        djpl_infos = self.deejayd.create_recorded_playlist(djplname,\
                "magic").get_contents()
        djpl = self.deejayd.get_recorded_playlist(djpl_infos["pl_id"],\
                djplname, "magic")
        filter = Equals('genre', self.test_audiodata.getRandomGenre())
        rnd_filter = Equals('genre', self.testdata.getRandomString())

        # add filter
        djpl.add_filter(filter).get_contents()
        # verify playlist
        ans = djpl.get()
        self.assertEqual(len(ans.get_filter()), 1)
        self.failUnless(len(ans.get_medias()) > 0)
        self.failUnless(filter.equals(ans.get_filter()[0]))

        # add random filter
        djpl.remove_filter(filter).get_contents()
        djpl.add_filter(rnd_filter).get_contents()
        # verify playlist
        ans = djpl.get()
        self.assertEqual(len(ans.get_filter()), 1)
        self.assertEqual(len(ans.get_medias()), 0)
        self.failUnless(rnd_filter.equals(ans.get_filter()[0]))

        # add filter and set property
        djpl.clear_filters().get_contents()
        djpl.add_filter(filter).get_contents()
        djpl.set_property("use-limit", "1").get_contents()
        djpl.set_property("limit-value", "1").get_contents()
        # verify playlist
        ans = djpl.get()
        self.assertEqual(len(ans.get_filter()), 1)
        self.assertEqual(len(ans.get_medias()), 1)
        self.failUnless(filter.equals(ans.get_filter()[0]))

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
            myq.append(self.test_audiodata.medias[song_path].tags["uri"])
            ans = q.add_path(song_path)
            self.failUnless(ans.get_contents())

        ddq = q.get()

        ddq_uris = [song['uri'] for song in ddq.get_medias()]
        for song_uri in myq:
            self.failUnless(song_uri in ddq_uris)

        random.seed(time.time())
        songs_to_delete = random.sample(myq, how_many_songs / 3)
        ans = q.del_songs([song['id'] for song in ddq.get_medias()\
                                      if song['uri'] in songs_to_delete])
        self.failUnless(ans.get_contents())

        ddq = q.get()
        ddq_uris = [song['uri'] for song in ddq.get_medias()]
        for song_uri in myq:
            if song_uri in songs_to_delete:
                self.failIf(song_uri in ddq_uris)
            else:
                self.failUnless(song_uri in ddq_uris)

        ans = q.clear()
        self.failUnless(ans.get_contents())
        ddq = q.get()
        self.assertEqual(ddq.get_medias(), [])

    def testPanel(self):
        """ Test panel source actions """
        panel = self.deejayd.get_panel()

        # get panel tags
        tags = panel.get_panel_tags().get_contents()
        for tag in tags:
            self.failUnless(tag in ['genre', 'artist',\
                    'various_artist', 'album'])

        # set filter
        bad_tag = self.testdata.getRandomString()
        random_str = self.testdata.getRandomString()
        ans = panel.set_panel_filters(bad_tag, [random_str]) # random tags
        self.assertRaises(DeejaydError, ans.get_contents)

        tag = self.testdata.getRandomElement(tags)
        panel.set_panel_filters(tag, [random_str]).get_contents()
        ans = panel.get()
        self.assertEqual([], ans.get_medias())

        # remove bad filter
        panel.remove_panel_filters(tag).get_contents()
        ans = panel.get()
        self.failUnless(len(ans.get_medias()) > 0)

        # get correct value for a tag
        result = self.deejayd.mediadb_list(tag, None).get_contents()
        value = self.testdata.getRandomElement(result)
        panel.set_panel_filters(tag, [value]).get_contents()
        ans = panel.get()
        self.failUnless(len(ans.get_medias()) > 0)

        # clear tag
        panel.clear_panel_filters().get_contents()
        ans = panel.get()
        self.failUnless(len(ans.get_medias()) > 0)

        # set search
        ans = panel.set_search_filter(bad_tag, random_str) # random tags
        self.assertRaises(DeejaydError, ans.get_contents)

        search_tag = self.testdata.getRandomElement(['title', 'album',\
                'genre', 'artist'])
        panel.set_search_filter(search_tag, random_str).get_contents()
        ans = panel.get()
        self.assertEqual([], ans.get_medias())

        # clear search
        panel.clear_search_filter().get_contents()
        ans = panel.get()
        self.failUnless(len(ans.get_medias()) > 0)

        # test sort
        result = panel.set_sorts([(bad_tag, 'ascending')])
        self.assertRaises(DeejaydError, result.get_contents)

        tag = self.testdata.getRandomElement(['title', 'rating', 'genre'])
        media_list = [m[tag] for m in ans.get_medias()]
        media_list.sort()
        panel.set_sorts([(tag, 'ascending')]).get_contents()
        ans = panel.get()
        for idx, m in enumerate(ans.get_medias()):
            self.assertEqual(m[tag], media_list[idx])

        # save a playlist and update active list
        djpl = self.deejayd.get_playlist()
        ans = self.deejayd.get_audio_dir()
        dir = self.testdata.getRandomElement(ans.get_directories())
        djpl.add_paths([dir]).get_contents()
        test_pl_name = self.testdata.getRandomString()
        djpl.save(test_pl_name).get_contents()
        pl_list = self.deejayd.get_playlist_list().get_medias()
        if len(pl_list) != 1:
            raise DeejaydError("playlist not saved")

        # save a playlist and update active list
        bad_plid = self.testdata.getRandomInt(2000, 1000)
        ans = panel.set_active_list("playlist", bad_plid)
        self.assertRaises(DeejaydError, ans.get_contents)

        panel.set_active_list("playlist", pl_list[0]["id"]).get_contents()
        panel_list = panel.get_active_list().get_contents()
        self.assertEqual(panel_list["type"], "playlist")
        self.assertEqual(panel_list["value"], pl_list[0]["id"])

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
        ans = self.deejayd.get_video_dir(dir)
        self.assertEqual(len(video_list), len(ans.get_files()))
        # sort videolist content
        sort = [["rating", "ascending"]]
        video_obj.set_sorts(sort).get_contents()
        video_list = video_obj.get()
        self.assertEqual(video_list.get_sort(), sort)
        # set bad sort
        rnd_sort = [(self.testdata.getRandomString(), "ascending")]
        ans = video_obj.set_sorts(rnd_sort)
        self.assertRaises(DeejaydError, ans.get_contents)

        # search a wrong title
        rand = self.testdata.getRandomString()
        video_obj.set(rand, "search").get_contents()
        video_list = video_obj.get().get_medias()
        self.assertEqual(len(video_list), 0)

    def testMediaRating(self):
        """Test media rating method"""
        # wrong media id
        random_id = self.testdata.getRandomInt(2000, 1000)
        ans = self.deejayd.set_media_rating([random_id], "2", "audio")
        self.assertRaises(DeejaydError, ans.get_contents)

        ans = self.deejayd.get_audio_dir()
        files = ans.get_files()
        file_ids = [f["media_id"] for f in files]
        # wrong rating
        ans = self.deejayd.set_media_rating(file_ids, "9", "audio")
        self.assertRaises(DeejaydError, ans.get_contents)
        # wrong library
        rand_lib = self.testdata.getRandomString()
        ans = self.deejayd.set_media_rating(file_ids, "2", rand_lib)
        self.assertRaises(DeejaydError, ans.get_contents)

        ans =  self.deejayd.set_media_rating(file_ids, "4", "audio")
        self.failUnless(ans.get_contents())
        ans = self.deejayd.get_audio_dir()
        files = ans.get_files()
        for f in files:
            self.assertEqual(4, int(f["rating"]))

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
        self.assertEqual(ans.get_medias(), [])

        # search a known terms
        file = self.testdata.getRandomElement(song_files)
        ans = self.deejayd.audio_search(file["title"], "title")
        self.failUnless(len(ans.get_medias()) > 0)

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
        ans = self.deejayd.set_option("playlist", opt, 1)
        self.assertRaises(DeejaydError, ans.get_contents)
        ans = self.deejayd.set_option(opt, "repeat", 1)
        self.assertRaises(DeejaydError, ans.get_contents)

        ans = self.deejayd.set_option("webradio", "playorder", "inorder")
        self.assertRaises(DeejaydError, ans.get_contents)

        # set playlist option
        ans = self.deejayd.set_option("playlist", "playorder", "random")
        ans.get_contents()
        status = self.deejayd.get_status().get_contents()
        self.assertEqual(status["playlistplayorder"], "random")
        # set video option
        ans = self.deejayd.set_option("video", "repeat", "1")
        ans.get_contents()
        status = self.deejayd.get_status().get_contents()
        self.assertEqual(status["videorepeat"], 1)

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
        djpl.add_paths([dir]).get_contents()

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
        self.deejayd.set_player_option("av_offset", 100).get_contents()
        ans = self.deejayd.set_player_option(self.testdata.getRandomString(),0)
        self.assertRaises(DeejaydError, ans.get_contents)

        self.deejayd.stop().get_contents()

    def testDvd(self):
        """ Test dvd commands"""
        status = self.deejayd.get_status().get_contents()
        dvd_id = status["dvd"]

        self.deejayd.dvd_reload().get_contents()
        status = self.deejayd.get_status().get_contents()
        self.assertEqual(status["dvd"], dvd_id + 1)

    def test_mediadb_list(self):
        """Test db queries for tags listing."""

        tag = 'artist'
        filter = Or(Equals('genre', self.test_audiodata.getRandomGenre()),
                    Equals('genre', self.test_audiodata.getRandomGenre()))

        expected_tag_list = []

        for song_info in self.test_audiodata.medias.values():
            matches = False
            for f in filter.filterlist:
                if song_info.tags['genre'] == f.pattern:
                    matches = True
            if matches:
                if song_info.tags[tag] not in expected_tag_list:
                    expected_tag_list.append(song_info.tags[tag])

        result = self.deejayd.mediadb_list(tag, filter)

        for tagvalue in expected_tag_list:
            self.failUnless(tagvalue in result)


class InterfaceSubscribeTests:
    """Test the subscription interface. This is for the core and the async client only."""

    def test_subscription(self):
        """Checks that signals subscriptions get in and out."""
        server_notification = threading.Event()

        sub_id = self.deejayd.subscribe('player.status',
                                        lambda x: server_notification.set())
        self.failUnless((sub_id, 'player.status')\
                        in self.deejayd.get_subscriptions().items())

        self.deejayd.unsubscribe(sub_id)
        self.failUnless((sub_id, 'player.status')\
                        not in self.deejayd.get_subscriptions().items())

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
                        (self.deejayd.set_option, ("playlist", 'repeat', 1)),
                        (self.deejayd.set_option, ('video', "playorder",\
                                                   "random")),
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

        trigger_list = ((djpl.add_paths, ([dir], )),
                        (djpl.shuffle, ()),
                        (djpl.clear, ()),
                       )

        for trig in trigger_list:
            self.generic_sub_bcast_test('player.plupdate', trig[0], trig[1])

    def test_sub_broadcast_playlist_listupdate(self):
        """Checks that playlist.listupdate signals are broadcasted."""

        djpl = self.deejayd.get_playlist()
        ans = self.deejayd.get_audio_dir()
        dir = self.testdata.getRandomElement(ans.get_directories())
        djpl.add_paths([dir]).get_contents()

        test_pl_name = self.testdata.getRandomString()
        test_pl_name2 = self.testdata.getRandomString()

        self.generic_sub_bcast_test('playlist.listupdate',
                                    djpl.save, (test_pl_name, ))

        retrievedPls = self.deejayd.get_playlist_list().get_medias()
        for pls in retrievedPls:
            if pls["name"] == test_pl_name:
                djpl_id = pls["id"]
                break
        trigger_list = (
                        (self.deejayd.erase_playlist, ([djpl_id], )),
                        (djpl.save, (test_pl_name2,)),
                       )

        for trig in trigger_list:
            self.generic_sub_bcast_test('playlist.listupdate', trig[0], trig[1])

    def test_sub_broadcast_playlist_update(self):
        """Checks that playlist.update signals are broadcasted."""
        ans = self.deejayd.get_audio_dir()
        dir = self.testdata.getRandomElement(ans.get_directories())
        filter = Equals('genre', self.test_audiodata.getRandomGenre())

        st_pl_name = self.testdata.getRandomString()
        mg_pl_name = self.testdata.getRandomString()

        st_pl_infos = self.deejayd.create_recorded_playlist(st_pl_name,\
                'static').get_contents()
        mg_pl_infos = self.deejayd.create_recorded_playlist(mg_pl_name,\
                'magic').get_contents()

        st_djpl = self.deejayd.get_recorded_playlist(st_pl_infos["pl_id"],\
                st_pl_name, 'static')
        mg_djpl = self.deejayd.get_recorded_playlist(mg_pl_infos["pl_id"],\
                mg_pl_name, 'magic')

        trigger_list = (
                        (st_djpl.add_path, (dir,)),
                        (mg_djpl.add_filter, (filter,)),
                        (mg_djpl.remove_filter, (filter,)),
                        (mg_djpl.set_property, ('use-limit', '1')),
                       )
        for trig in trigger_list:
            self.generic_sub_bcast_test('playlist.update', trig[0], trig[1])

    def test_sub_broadcast_panel_update(self):
        """Checks that panel.update signals are broadcasted."""

        # first save a playlist
        djpl = self.deejayd.get_playlist()
        ans = self.deejayd.get_audio_dir()
        dir = self.testdata.getRandomElement(ans.get_directories())
        djpl.add_paths([dir]).get_contents()
        test_pl_name = self.testdata.getRandomString()
        djpl.save(test_pl_name).get_contents()
        pl_list = self.deejayd.get_playlist_list().get_medias()
        if len(pl_list) != 1:
            raise DeejaydError("playlist not saved")

        djpn = self.deejayd.get_panel()

        trigger_list = (
                        (djpn.set_active_list, ("playlist", pl_list[0]["id"])),
                        (djpn.set_active_list, ("panel", "0")),
                        (djpn.set_panel_filters, ("genre", "zboub")),
                        (djpn.clear_panel_filters, []),
                        (djpn.set_sorts, ([("genre", "ascending")],)),
                       )

        for trig in trigger_list:
            self.generic_sub_bcast_test('panel.update', trig[0], trig[1])

    def test_sub_broadcast_video_update(self):
        """Checks that video.update signals are broadcasted."""

        djvideo = self.deejayd.get_video()
        ans = self.deejayd.get_video_dir()
        dir = self.testdata.getRandomElement(ans.get_directories())

        trigger_list = (
                        (djvideo.set, (dir, "directory")),
                        (djvideo.set_sorts, ([("title", "ascending")],)),
                       )

        for trig in trigger_list:
            self.generic_sub_bcast_test('video.update', trig[0], trig[1])

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

        self.generic_sub_bcast_test('queue.update', q.add_paths, ([dir], ))

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
