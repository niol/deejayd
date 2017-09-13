# Deejayd, a media player daemon
# Copyright (C) 2007-2017 Mickael Royer <mickael.royer@gmail.com>
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

    def __load_videos(self):
        video_obj = self.deejayd.videopls

        # choose directory
        ans = self.deejayd.videolib.get_dir_content()
        dir_obj = self.testdata.get_random_element(ans["directories"])
        video_obj.load_folders([dir_obj["id"]])

    def __load_songs(self):
        djpl = self.deejayd.audiopls
        ans = self.deejayd.audiolib.get_dir_content()
        dir_obj = self.testdata.get_random_element(ans["directories"])
        djpl.load_folders([dir_obj["id"]])

    def __get_pl_content(self):
        return self.deejayd.audiopls.get()

    def __test_play_toggle(self, pls="audiopls"):
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
        """Test player.play_toggle command for songs"""
        self.__load_songs()
        self.__test_play_toggle()

    @require_video_support
    def testPlayToggleVideo(self):
        """Test play_toggle command for videos"""
        self.__load_videos()
        self.__test_play_toggle(pls="videopls")

    def testPlayStop(self):
        """Test play, pause and stop command"""
        self.__load_songs()
        # test play command
        self.deejayd.player.go_to(0, "pos", "audiopls")
        self.assertEqual(self.deejayd.player.get_status()["state"], "play")

        # test pause command
        self.deejayd.player.pause()
        time.sleep(0.2)
        self.assertEqual(self.deejayd.player.get_status()["state"], "pause")

        # test stop command
        self.deejayd.player.stop()
        time.sleep(0.2)
        self.assertEqual(self.deejayd.get_status()["state"], "stop")

    def testNextPreviousGetPlaying(self):
        """Test next, previous and get_playing command"""
        def is_song_equals(song1, song2):
            self.assertTrue(song1["m_id"] == song2["m_id"])
            self.assertTrue(song1["id"] == song2["id"])

        self.__load_songs()
        songs = self.__get_pl_content()

        # next command
        self.deejayd.player.go_to(0, "pos", "audiopls")
        time.sleep(0.2)
        self.deejayd.player.next()
        time.sleep(0.2)
        current = self.deejayd.player.get_playing()

        self.assertEqual(self.deejayd.get_status()["state"], "play")
        is_song_equals(songs[1], current)

        # previous command
        self.deejayd.player.previous()
        time.sleep(0.2)
        current = self.deejayd.player.get_playing()
        is_song_equals(songs[0], current)
        self.deejayd.player.stop()

    def testSetVolume(self):
        """Test setVolume command"""
        player = self.deejayd.player

        # wrong volume value
        vol = self.testdata.get_random_element(range(1000, 2000))
        self.assertAckCmd(player.set_volume(vol))
        status = self.deejayd.player.get_status()
        self.assertEqual(status["volume"], 100)

        # correct volume value
        vol = self.testdata.get_random_element(range(0, 80))
        self.assertAckCmd(player.set_volume(vol))
        status = self.deejayd.player.get_status()
        self.assertEqual(status["volume"], vol)

        # test relative option
        step = self.testdata.get_random_element(range(1, 10))
        self.assertAckCmd(player.set_volume(step, True))
        status = self.deejayd.player.get_status()
        self.assertEqual(status["volume"], vol+step)

    def testSeek(self):
        """Test seek command"""
        self.__load_songs()
        self.deejayd.player.go_to(0, "pos", "audiopls")
        time.sleep(0.1)
        self.deejayd.player.seek(1)

        time.sleep(0.1)
        status = self.deejayd.player.get_status()
        self.assertTrue(int(status["time"].split(":")[0]) >= 1)

    @require_video_support
    def testPlayerVideoOptions(self):
        """Test player video options commands"""
        opts = [
            "current-audio",
            "current-sub",
            "av-offset",
            "sub-offset",
            "zoom",
            "aspect-ratio",
        ]
        video_opts = self.deejayd.player.get_available_video_options()
        for key in opts:
            self.assertTrue(video_opts[key] in (True, False))

        self.__load_videos()
        player = self.deejayd.player
        self.deejayd.player.go_to(0, "pos", "videopls")
        time.sleep(0.1)

        # try a wrong option
        rand_opt = self.testdata.get_random_string()
        self.assertRaises(DeejaydError, player.set_video_option, rand_opt, 1)

        for opt in opts:
            if video_opts[opt]:
                # first try with a wrong value
                rand_value = self.testdata.get_random_string()
                self.assertRaises(DeejaydError, player.set_video_option,
                                  opt, rand_value)

                if opt == "zoom":
                    player.set_video_option(opt, "200")
