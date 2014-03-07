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

import time

from deejayd import DeejaydError
from testdeejayd.interfaces import require_video_support, _TestInterfaces

class PlayerInterfaceTests(_TestInterfaces):

    def __loadVideos(self):
        video_obj = self.deejayd.videopls
        player = self.deejayd.player

        # choose directory
        ans = self.deejayd.videolib.get_dir_content()
        dir = self.testdata.getRandomElement(ans["directories"])
        video_obj.load_folders([dir["id"]])

    def __loadSongs(self):
        djpl = self.deejayd.audiopls
        ans = self.deejayd.audiolib.get_dir_content()
        dir = self.testdata.getRandomElement(ans["directories"])
        djpl.load_folders([dir["id"]])

    def __getPlContent(self):
        djpl = self.deejayd.audiopls
        return djpl.get()

    def __testPlayToggle(self, pls="audiopls"):
        self.deejayd.player.go_to(0, "pos", pls)
        # verify status
        time.sleep(0.2)
        self.assertEqual(self.deejayd.player.get_status()["state"], "play")
        # pause
        self.deejayd.player.play_toggle()
        # verify status
        time.sleep(0.2)
        self.assertEqual(self.deejayd.player.get_status()["state"], "pause")

    def testPlayToggleAudio(self):
        """Test play_toggle command for songs"""
        self.__loadSongs()
        self.__testPlayToggle()

    @require_video_support
    def testPlayToggleVideo(self):
        """Test play_toggle command for videos"""
        self.__loadVideos()
        self.__testPlayToggle(pls="videopls")

    def testPlayStop(self):
        """Test play, pause and stop command"""
        self.__loadSongs()
        # test play command
        self.deejayd.player.go_to(0, "pos", "audiopls")
        self.assertEqual(self.deejayd.player.get_status()["state"], "play")

        # test pause command
        time.sleep(0.1)
        self.deejayd.player.pause()
        self.assertEqual(self.deejayd.player.get_status()["state"], "pause")

        # test stop command
        time.sleep(0.1)
        self.deejayd.player.stop()
        self.assertEqual(self.deejayd.get_status()["state"], "stop")

    def testNextPreviousGetPlaying(self):
        """Test next, previous and get_playing command"""
        def is_song_equals(song1, song2):
            self.assertTrue(song1["media_id"] == song2["media_id"])
            self.assertTrue(song1["id"] == song2["id"])

        self.__loadSongs()
        songs = self.__getPlContent()

        # next command
        self.deejayd.player.go_to(0, "pos", "audiopls")
        time.sleep(0.1)
        self.deejayd.player.next()
        time.sleep(0.1)
        current = self.deejayd.player.get_playing()

        self.assertEqual(self.deejayd.get_status()["state"], "play")
        is_song_equals(songs[1], current)

        # previous command
        time.sleep(0.1)
        self.deejayd.player.previous()
        time.sleep(0.1)
        current = self.deejayd.player.get_playing()
        is_song_equals(songs[0], current)
        self.deejayd.player.stop()

    def testSetVolume(self):
        """Test setVolume command"""
        player = self.deejayd.player

        # wrong volume value
        vol = self.testdata.getRandomElement(range(1000, 2000))
        self.assertRaises(DeejaydError, player.set_volume, vol)

        # correct volume value
        vol = self.testdata.getRandomElement(range(0, 101))
        self.assertAckCmd(player.set_volume(vol))
        status = self.deejayd.player.get_status()
        self.assertEqual(status["volume"], vol)

    def testSeek(self):
        """Test seek command"""
        self.__loadSongs()
        self.deejayd.player.go_to(0, "pos", "audiopls")
        time.sleep(0.1)
        self.deejayd.player.seek(1)

        status = self.deejayd.player.get_status()
        self.assertTrue(int(status["time"].split(":")[0]) >= 1)

    @require_video_support
    def testGetAvailableVideoOptions(self):
        """Test get_available_video_options command"""
        video_opts = self.deejayd.player.get_available_video_options()
        for key in ('audio_lang', 'sub_lang', 'av_offset', 'sub_offset',\
                'zoom', 'aspect_ratio'):
            self.assertTrue(video_opts[key] in (True, False))

    @require_video_support
    def testSetVideoOption(self):
        """Test set_video_option command"""
        self.__loadVideos()
        player = self.deejayd.player
        self.deejayd.player.go_to(0, "pos", "videopls")
        time.sleep(0.1)

        # try a wrong option
        rand_opt = self.testdata.getRandomString()
        self.assertRaises(DeejaydError, player.set_video_option, rand_opt, 1)

        video_opts = player.get_available_video_options()
        for opt in ('audio_lang', 'sub_lang', 'av_offset', 'sub_offset',\
                'zoom', 'aspect_ratio'):
            if video_opts[opt]:
                # first try with a wrong value
                rand_value = self.testdata.getRandomString()
                self.assertRaises(DeejaydError, player.set_video_option, opt,\
                        rand_value)

                if opt == "zoom":
                    player.set_video_option(opt, "200")

# vim: ts=4 sw=4 expandtab
