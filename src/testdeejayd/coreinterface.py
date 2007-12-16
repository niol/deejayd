import time, random

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
        known_keys = ("queue","playlist","dvd","webradio","video")
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
            ans = q.add_song(song_path)
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
        opt = self.testdata.getRandomElement(('random','repeat','fullscreen'))
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

        # test get_current command
        cur = self.deejayd.get_current().get_medias()
        self.assertEqual(len(cur), 1)

        self.deejayd.stop().get_contents()

    def testVideoPlayer(self):
        """ Test player commands (play, pause,...) for video """
        # set video mode
        self.deejayd.set_mode("video").get_contents()

        # choose a wrong directory
        rand_dir = self.testdata.getRandomString()
        ans = self.deejayd.set_video_dir(rand_dir)
        self.assertRaises(DeejaydError, ans.get_contents)

        # choose a correct directory
        ans = self.deejayd.get_video_dir()
        dir = self.testdata.getRandomElement(ans.get_directories())
        self.deejayd.set_video_dir(dir).get_contents()

        # play video file
        self.deejayd.play_toggle().get_contents()
        # verify status
        status = self.deejayd.get_status().get_contents()
        self.assertEqual(status["state"], "play")

        self.deejayd.stop().get_contents()

    def testDvd(self):
        """ Test dvd commands"""
        status = self.deejayd.get_status().get_contents()
        dvd_id = status["dvd"]

        self.deejayd.dvd_reload().get_contents()
        status = self.deejayd.get_status().get_contents()
        self.assertEqual(status["dvd"], dvd_id + 1)

# vim: ts=4 sw=4 expandtab
