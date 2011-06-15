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

from deejayd import DeejaydError
from deejayd.mediafilters import *


class InterfaceTests:
    """Test the deejayd daemon core interface, this test suite is to be used for testing the core facade and the client library."""

    def assertAckCmd(self, cmd_res):
        raise NotImplementedError

    def testSetMode(self):
        """Test setMode command"""

        # ask an unknown mode
        mode_name = self.testdata.getRandomString()
        self.assertRaises(DeejaydError, self.deejayd.set_mode,mode_name)

        # ask a known mode
        known_mode = 'playlist'
        self.assertAckCmd(self.deejayd.set_mode(known_mode))

        # Test if the mode has been set
        self.assertEqual(self.deejayd.get_status()['mode'], known_mode)

    def testGetMode(self):
        """Test getMode command"""
        known_keys = ("playlist", "panel", "dvd", "webradio", "video")
        ans = self.deejayd.get_modes()
        for k in known_keys:
            self.failUnless(k in ans.keys())
            self.failUnless(ans[k] in (True, False))

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
        djpl = self.deejayd.playlist
        ans = djpl.get()
        self.assertEqual(ans["medias"], pl)

        self.assertRaises(DeejaydError,
                          djpl.add_path, self.testdata.getRandomString())

        # Add songs to playlist
        howManySongs = 3
        for songPath in self.test_audiodata.getRandomSongPaths(howManySongs):
            pl.append(self.test_audiodata.medias[songPath].tags["uri"])
            self.assertAckCmd(djpl.add_path([songPath]))

        # Check for the playlist to be of appropriate length
        self.assertEqual(self.deejayd.get_status()['playlistlength'],
                         howManySongs)

        ans = djpl.save(djplname)
        djpl_id = ans["playlist_id"]

        # Check for the saved playslit to be available
        retrievedPls = self.deejayd.recpls.get_list()
        self.failUnless(djplname in [p["name"] for p in retrievedPls])

        # Retrieve the saved playlist
        retrievedPl = self.deejayd.recpls.get_content(djpl_id)["medias"]
        for song_nb in range(len(pl)):
            self.assertEqual(pl[song_nb], retrievedPl[song_nb]['uri'])

    def testPlaylistActions(self):
        """Test actions on current playlist."""
        djpl = self.deejayd.playlist
        howManySongs = 4
        self.assertAckCmd(djpl.add_path(\
                self.test_audiodata.getRandomSongPaths(howManySongs)))

        content = djpl.get()["medias"]
        song = self.testdata.getRandomElement(content)
        # shuffle the playlist
        self.assertAckCmd(djpl.shuffle())
        # move this song
        self.assertAckCmd(djpl.move([song["id"]], 1))
        # delete a song
        djpl.remove([song["id"]])
        content = djpl.get()["medias"]
        self.assertEqual(len(content), howManySongs-1)

    def testSavedStaticPlaylistActions(self):
        """Test action on saved static playlist"""
        djplname = self.testdata.getRandomString()
        djpl = self.deejayd.playlist
        howManySongs = 3
        # Add songs to playlist
        for songPath in self.test_audiodata.getRandomSongPaths(howManySongs):
            self.assertAckCmd(djpl.add_path([songPath]))
        # save playlist
        ans = djpl.save(djplname)
        djpl_id = ans["playlist_id"]

        # add songs in the saved playlist
        recpls = self.deejayd.recpls
        for songPath in self.test_audiodata.getRandomSongPaths(howManySongs):
            # add twice the same song
            self.assertAckCmd(recpls.static_add(djpl_id, (songPath, songPath)))
        content = recpls.get_content(djpl_id)["medias"]
        self.assertEqual(len(content), howManySongs*3)

    def testSavedMagicPlaylistActions(self):
        """Test action on saved magic playlist"""
        recpls = self.deejayd.recpls

        djplname = self.testdata.getRandomString()
        djpl_infos = recpls.create(djplname, "magic")
        djpl_id = djpl_infos["pl_id"]
        filter = Equals('genre', self.test_audiodata.getRandomGenre())
        rnd_filter = Equals('genre', self.testdata.getRandomString())

        # add filter
        recpls.magic_add_filter(djpl_id, filter)
        # verify playlist
        ans = recpls.get_content(djpl_id)
        self.assertEqual(len(ans["filter"]), 1)
        self.failUnless(len(ans["medias"]) > 0)
        self.failUnless(filter.equals(ans["filter"][0]))

        # add random filter
        recpls.magic_remove_filter(djpl_id, filter)
        recpls.magic_add_filter(djpl_id, rnd_filter)
        # verify playlist
        ans = recpls.get_content(djpl_id)
        self.assertEqual(len(ans["filter"]), 1)
        self.assertEqual(len(ans["medias"]), 0)
        self.failUnless(rnd_filter.equals(ans["filter"][0]))

        # add filter and set property
        recpls.magic_clear_filter(djpl_id)
        recpls.magic_add_filter(djpl_id, filter)
        recpls.magic_set_property(djpl_id, "use-limit", "1")
        recpls.magic_set_property(djpl_id, "limit-value", "1")
        # verify playlist
        ans = recpls.get_content(djpl_id)
        self.assertEqual(len(ans["filter"]), 1)
        self.assertEqual(len(ans["medias"]), 1)
        self.failUnless(filter.equals(ans["filter"][0]))

    def testWebradioAddRetrieve(self):
        """Save a webradio and check it is in the list, then delete it."""
        wr_list = self.deejayd.webradio

        # try to set wrong source
        self.assertRaises(DeejaydError,
                          wr_list.set_source, self.testdata.getRandomString())
        # set local source
        self.assertAckCmd(wr_list.set_source('local'))
        # local does not have categorie, raise DeejaydError if we try to get it
        self.assertRaises(DeejaydError, wr_list.get_source_categories, 'local')


        # Test for bad URI and inexistant playlist
        for badURI in [[self.testdata.getRandomString(50)],\
                   ['http://' + self.testdata.getRandomString(50) + '.pls']]:
            self.assertRaises(DeejaydError, wr_list.local_add,
                              self.testdata.getRandomString(), badURI)

        # Add correct URI
        testWrName = self.testdata.getRandomString()
        testWrUrls = []
        for urlCount in range(self.testdata.getRandomInt(10)):
            testWrUrls.append('http://' + self.testdata.getRandomString(50))
        self.assertAckCmd(wr_list.local_add(testWrName, testWrUrls))

        # verify recorded webradios
        wr_names = [wr['title'] for wr in wr_list.get()["medias"]]
        self.failUnless(testWrName in wr_names)
        retrievedWr = [wr for wr in wr_list.get()["medias"]\
                          if wr['title'] == testWrName][0]
        for url in testWrUrls:
            self.failUnless(url in retrievedWr['urls'])

        # erase unknown wb
        self.assertRaises(DeejaydError, wr_list.local_delete, (51,))

        # erase known wb
        self.assertAckCmd(wr_list.local_delete((retrievedWr['id'],)))

        wr_list = wr_list.get()["medias"]
        self.failIf(testWrName in [wr['title'] for wr in wr_list])

    def testQueue(self):
        """Add songs to the queue, try to retrieve it, delete some songs in it, then clear it."""
        q = self.deejayd.queue

        myq = []
        how_many_songs = 10
        for song_path in self.test_audiodata.getRandomSongPaths(how_many_songs):
            myq.append(self.test_audiodata.medias[song_path].tags["uri"])
            self.assertAckCmd(q.add_path([song_path]))

        ddq = q.get()
        ddq_uris = [song['uri'] for song in ddq["medias"]]
        for song_uri in myq:
            self.failUnless(song_uri in ddq_uris)

        random.seed(time.time())
        songs_to_delete = random.sample(myq, how_many_songs / 3)
        self.assertAckCmd(q.remove([song['id'] for song in ddq["medias"]\
                                      if song['uri'] in songs_to_delete]))

        ddq = q.get()
        ddq_uris = [song['uri'] for song in ddq["medias"]]
        for song_uri in myq:
            if song_uri in songs_to_delete:
                self.failIf(song_uri in ddq_uris)
            else:
                self.failUnless(song_uri in ddq_uris)

        self.assertAckCmd(q.clear())
        self.assertEqual(q.get()["medias"], [])

    def testPanel(self):
        """ Test panel source actions """
        panel = self.deejayd.panel

        # get panel tags
        tags = panel.get_tags()
        for tag in tags:
            self.failUnless(tag in ['genre', 'artist',\
                    'various_artist', 'album'])

        # set filter
        bad_tag = self.testdata.getRandomString()
        random_str = self.testdata.getRandomString()
        self.assertRaises(DeejaydError, panel.set_filter,
                          bad_tag, [random_str]) # random tags

        tag = self.testdata.getRandomElement(tags)
        self.assertAckCmd(panel.set_filter(tag, [random_str]))
        self.assertEqual([], panel.get()["medias"])

        # remove bad filter
        self.assertAckCmd(panel.remove_filter(tag))
        self.failUnless(len(panel.get()["medias"]) > 0)

        # get correct value for a tag
        result = self.deejayd.audiolib.tag_list(tag, None)
        value = self.testdata.getRandomElement(result)
        self.assertAckCmd(panel.set_filter(tag, [value]))
        self.failUnless(len(panel.get()["medias"]) > 0)

        # clear tag
        panel.clear_filters()
        self.failUnless(len(panel.get()["medias"]) > 0)

        # set search
        self.assertRaises(DeejaydError, panel.set_search_filter,
                          bad_tag, random_str) # random tags

        search_tag = self.testdata.getRandomElement(['title', 'album',\
                'genre', 'artist'])
        self.assertAckCmd(panel.set_search_filter(search_tag, random_str))
        self.assertEqual([], panel.get()["medias"])

        # clear search
        self.assertAckCmd(panel.clear_search_filter())
        self.failUnless(len(panel.get()["medias"]) > 0)

        # test sort
        self.assertRaises(DeejaydError, panel.set_sort,
                          [(bad_tag, 'ascending')])

        tag = self.testdata.getRandomElement(['title', 'rating', 'genre'])
        media_list = [m[tag] for m in panel.get()["medias"]]
        media_list.sort()
        panel.set_sort([(tag, 'ascending')])
        for idx, m in enumerate(panel.get()["medias"]):
            self.assertEqual(m[tag], media_list[idx])

        # save a playlist and update active list
        djpl = self.deejayd.playlist
        ans = self.deejayd.audiolib.get_dir_content()
        dir = self.testdata.getRandomElement(ans["directories"])
        self.assertAckCmd(djpl.add_path([dir]))
        test_pl_name = self.testdata.getRandomString()
        ans = djpl.save(test_pl_name)
        pl_list = self.deejayd.recpls.get_list()
        if len(pl_list) != 1:
            raise DeejaydError("playlist not saved")

        # save a playlist and update active list
        bad_plid = self.testdata.getRandomInt(2000, 1000)
        self.assertRaises(DeejaydError, panel.set_active_list,
                          "playlist", bad_plid)

        self.assertAckCmd(panel.set_active_list("playlist", pl_list[0]["id"]))
        panel_list = panel.get_active_list()
        self.assertEqual(panel_list["type"], "playlist")
        self.assertEqual(panel_list["value"], pl_list[0]["id"])

    def testVideo(self):
        """ Test video source actions """
        if self.video_support:
            video_obj = self.deejayd.video
            # choose a wrong directory
            rand_dir = self.testdata.getRandomString()
            self.assertRaises(DeejaydError, video_obj.set,
                              rand_dir, "directory")

            # get contents of root dir and try to set video directory
            ans = self.deejayd.videolib.get_dir_content()
            dir = self.testdata.getRandomElement(ans["directories"])
            self.assertAckCmd(video_obj.set(dir, "directory"))

            # test videolist content
            self.assertEqual(len(video_obj.get()["medias"]), len(ans["files"]))
            # sort videolist content
            sort = [["rating", "ascending"]]
            self.assertAckCmd(video_obj.set_sort(sort))
            self.assertEqual(video_obj.get()["sort"], sort)
            # set bad sort
            rnd_sort = [(self.testdata.getRandomString(), "ascending")]
            self.assertRaises(DeejaydError, video_obj.set_sort, rnd_sort)

            # search a wrong title
            rand = self.testdata.getRandomString()
            video_obj.set(rand, "search")
            self.assertEqual(len(video_obj.get()["medias"]), 0)
        else:
            try: video_obj = self.deejayd.video
            except AttributeError: # we test core
                pass
            else:
                self.assertRaises(DeejaydError, video_obj.get)

    def testMediaRating(self):
        """Test media rating method"""
        # wrong media id
        random_id = self.testdata.getRandomInt(2000, 1000)
        self.assertRaises(DeejaydError, self.deejayd.set_rating,
                          [random_id], "2", "audio")

        ans = self.deejayd.audiolib.get_dir_content()
        files = ans["files"]
        file_ids = [f["media_id"] for f in files]
        # wrong rating
        self.assertRaises(DeejaydError, self.deejayd.set_rating,
                          file_ids, "9", "audio")
        # wrong library
        rand_lib = self.testdata.getRandomString()
        self.assertRaises(DeejaydError, self.deejayd.set_rating,
                          file_ids, "2", rand_lib)

        self.assertAckCmd(self.deejayd.set_rating(file_ids, "4", "audio"))
        ans = self.deejayd.audiolib.get_dir_content()
        for f in ans["files"]:
            self.assertEqual(4, int(f["rating"]))

    def testAudioLibrary(self):
        """ Test request on audio library (get_audio_dir, search)"""
        audiolib = self.deejayd.audiolib

        # try to get contents of an unknown directory
        rand_dir = self.testdata.getRandomString()
        self.assertRaises(DeejaydError, audiolib.get_dir_content, rand_dir)

        # get contents of root dir and try to get content of a directory
        ans = audiolib.get_dir_content()
        dir = self.testdata.getRandomElement(ans["directories"])
        ans = audiolib.get_dir_content(dir)
        song_files = ans["files"]
        self.failUnless(len(ans["files"]) > 0)

        # search an unknown terms
        text = self.testdata.getRandomString()
        self.assertEqual(audiolib.search(text), [])

        # search a known terms
        file = self.testdata.getRandomElement(song_files)
        ans = audiolib.search(file["title"], "title")
        self.failUnless(len(ans) > 0)

    def testVideoLibrary(self):
        """ Test request on video library """
        if self.video_support:
            videolib = self.deejayd.videolib

            # try to get contents of an unknown directory
            rand_dir = self.testdata.getRandomString()
            self.assertRaises(DeejaydError, videolib.get_dir_content, rand_dir)

            # get contents of root dir and try to get content of a directory
            ans = videolib.get_dir_content()
            dir = self.testdata.getRandomElement(ans["directories"])
            ans = videolib.get_dir_content(dir)
            self.failUnless(len(ans["files"]) > 0)
        else:
            try: videolib = self.deejayd.videolib
            except AttributeError: # deejayd core
                pass
            else: # deejayd client
                self.assertRaises(DeejaydError, videolib.get_dir_content)

    def testSetOption(self):
        """ Test set_option commands"""
        # unknown option
        rnd_opt = self.testdata.getRandomString()
        self.assertRaises(DeejaydError, self.deejayd.set_option,
                          "playlist", rnd_opt, 1)
        self.assertRaises(DeejaydError, self.deejayd.set_option,
                          rnd_opt, "repeat", True)
        self.assertRaises(DeejaydError, self.deejayd.set_option,
                          "webradio", "playorder", "inorder")

        # set playlist option
        self.assertAckCmd(self.deejayd.set_option("playlist", "playorder", "random"))
        status = self.deejayd.get_status()
        self.assertEqual(status["playlistplayorder"], "random")
        # set video option
        if self.video_support:
            self.deejayd.set_option("video", "repeat", True)
            status = self.deejayd.get_status()
            self.assertEqual(status["videorepeat"], True)

    def testAudioPlayer(self):
        """ Test player commands (play, pause,...) for audio """
        # try to set volume
        vol = 30
        self.assertAckCmd(self.deejayd.player.set_volume(vol))
        status = self.deejayd.get_status()
        self.assertEqual(status["volume"], vol)

        # load songs in main playlist
        djpl = self.deejayd.playlist
        ans = self.deejayd.audiolib.get_dir_content()
        dir = self.testdata.getRandomElement(ans["directories"])
        djpl.add_path([dir])

        # play song
        self.deejayd.set_mode("playlist")
        self.deejayd.player.play_toggle()
        # verify status
        self.assertEqual(self.deejayd.get_status()["state"], "play")
        # pause
        self.deejayd.player.play_toggle()
        # verify status
        self.assertEqual(self.deejayd.get_status()["state"], "pause")
        self.deejayd.player.play_toggle()
        # next and previous
        self.deejayd.player.next()
        self.deejayd.player.previous()
        self.assertEqual(self.deejayd.get_status()["state"], "play")
        # seek command
        self.deejayd.player.seek(1)

        # test get_current command
        cur = self.deejayd.player.get_playing()
        self.failUnless(cur is not None)

        self.deejayd.player.stop()

    def testVideoPlayer(self):
        """ Test player commands (play, pause,...) for video """
        if self.video_support:
            video_obj = self.deejayd.video
            player = self.deejayd.player
            # set video mode
            self.deejayd.set_mode("video")

            # choose directory
            ans = self.deejayd.videolib.get_dir_content()
            dir = self.testdata.getRandomElement(ans["directories"])
            video_obj.set(dir, "directory")

            # play video file
            player.play_toggle()
            # verify status
            self.assertEqual(self.deejayd.get_status()["state"], "play")

            # test set_player_option cmd
            player.set_video_option("av_offset", 100)
            player.set_video_option("aspect_ratio","16:9")
            # bad option name
            self.assertRaises(DeejaydError, player.set_video_option, \
                              self.testdata.getRandomString(),0)
            # bad option value
            self.assertRaises(DeejaydError, player.set_video_option, \
                              "av_offset", self.testdata.getRandomString())

            player.stop()

    def testDvd(self):
        """ Test dvd commands"""
        # disable test if video support or dvd mode are disabled
        modes = self.deejayd.get_modes()
        if not self.video_support or not modes["dvd"]:
            return True

        dvd_id = self.deejayd.get_status()["dvd"]
        self.deejayd.dvd_reload()
        self.assertEqual(self.deejayd.get_status()["dvd"], dvd_id + 1)

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

        result = self.deejayd.audiolib.tag_list(tag, filter)

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
            ans.wait_for_answer()
        server_notification.wait(4)
        self.failUnless(server_notification.isSet(),
                        '%s signal was not broadcasted by %s.'\
                        % (signal_name, trigger.__name__))
        server_notification.clear()

        self.deejayd.unsubscribe(sub_id)

    def test_sub_broadcast_player_status(self):
        """Checks that player.status signals are broadcasted."""

        trigger_list = ((self.deejayd.player.play_toggle, ()),
                        (self.deejayd.set_option, ("playlist", 'repeat', True)),
                        (self.deejayd.set_option, ('panel', "playorder",\
                                                   "random")),
                        (self.deejayd.player.set_volume, (51, )),
                        (self.deejayd.player.seek, (5, )),
                       )

        for trig in trigger_list:
            self.generic_sub_bcast_test('player.status', trig[0], trig[1])

    def test_sub_broadcast_player_current(self):
        """Checks that player.current signals are broadcasted."""

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

        trigger_list = ((djpl.add_path, ([dir], )),
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
                                    djpl.save, (test_pl_name, ))

        retrievedPls = self.deejayd.recpls.get_list().wait_for_answer()
        for pls in retrievedPls:
            if pls["name"] == test_pl_name:
                djpl_id = pls["id"]
                break
        trigger_list = (
                        (self.deejayd.recpls.erase, ([djpl_id], )),
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

        st_pl_id = self.deejayd.recpls.create(st_pl_name,\
                'static').wait_for_answer()["pl_id"]
        mg_pl_id = self.deejayd.recpls.create(mg_pl_name,\
                'magic').wait_for_answer()["pl_id"]

        recpls = self.deejayd.recpls
        trigger_list = (
                        (recpls.static_add, (st_pl_id, [dir],)),
                        (recpls.magic_add_filter, (mg_pl_id, filter,)),
                        (recpls.magic_remove_filter, (mg_pl_id, filter,)),
                        (recpls.magic_set_property, (mg_pl_id,'use-limit','1'))
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
                        (djpn.set_active_list, ("playlist", pl_list[0]["id"])),
                        (djpn.set_active_list, ("panel", "0")),
                        (djpn.set_filter, ("genre", ["zboub"])),
                        (djpn.clear_filters, []),
                        (djpn.set_sort, ([("genre", "ascending")],)),
                       )

        for trig in trigger_list:
            self.generic_sub_bcast_test('panel.update', trig[0], trig[1])

    def test_sub_broadcast_video_update(self):
        """Checks that video.update signals are broadcasted."""

        if not self.video_support:
            return True

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
                                    wr_list.local_add,
                                    (test_wr_name, test_wr_urls))

        retrieved_wr = [wr for wr in wr_list.get().wait_for_answer()["medias"]\
                           if wr['title'] == test_wr_name][0]
        self.generic_sub_bcast_test('webradio.listupdate',
                                    wr_list.local_delete,
                                    ([retrieved_wr['id']], ))

    def test_sub_broadcast_queue_update(self):
        """Checks that queue.update signals are broadcasted."""

        q = self.deejayd.queue

        ans = self.deejayd.audiolib.get_dir_content().wait_for_answer()
        dir = self.testdata.getRandomElement(ans["directories"])

        self.generic_sub_bcast_test('queue.update', q.add_path, ([dir], ))

        retrieved_song_id = [song['id'] \
                for song in q.get().wait_for_answer()["medias"]]
        self.generic_sub_bcast_test('queue.update',
                                    q.remove, (retrieved_song_id, ))

    def test_sub_broadcast_dvd_update(self):
        """Checks that dvd.update signals are broadcasted."""
        # disable test if video support or dvd mode are disabled
        modes = self.deejayd.get_modes().wait_for_answer()
        if not self.video_support or not modes["dvd"]:
            return True
        self.generic_sub_bcast_test('dvd.update', self.deejayd.dvd.reload, ())

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
        if not self.video_support:
            return True
        # This is tested only using inotify support
        self.generic_sub_bcast_test('mediadb.vupdate',
                                    self.test_videodata.addMedia)


# vim: ts=4 sw=4 expandtab
