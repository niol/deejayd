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

from testdeejayd.interfaces import _TestInterfaces
from deejayd import DeejaydError

class CoreInterfaceTests(_TestInterfaces):

    def testPing(self):
        """Test ping command"""
        self.assertAckCmd(self.deejayd.ping())

    def testSetMode(self):
        """Test setMode command"""
        # ask an unknown mode
        mode_name = self.testdata.getRandomString()
        self.assertRaises(DeejaydError, self.deejayd.set_mode, mode_name)

        # ask for known modes
        known_modes = ['playlist', 'panel', 'webradio']
        if self.hasVideoSupport():
            known_modes.append('video')
        for known_mode in known_modes:
            self.assertAckCmd(self.deejayd.set_mode(known_mode))

            # Test if the mode has been set
            self.assertEqual(self.deejayd.get_status()['mode'], known_mode)

    def testGetModes(self):
        """Test getModes command"""
        known_keys = ("playlist", "panel", "webradio", "video")
        ans = self.deejayd.get_modes()
        for k in known_keys:
            self.assertTrue(k in ans.keys())
            self.assertTrue(ans[k] in (True, False))

    def testGetStats(self):
        """Test getStats command"""
        ans = self.deejayd.get_stats()
        keys = ["audio_library_update", "songs", "artists", "albums"]
        if self.hasVideoSupport():
            keys.append("video_library_update")
        for k in keys:
            self.assertTrue(k in ans.keys())

    def testGetStatus(self):
        """Test getStatus command"""
        ans = self.deejayd.get_status()
        keys = [
            "playlist",
            "playlistrepeat",
            "playlistplayorder",
            "playlistlength",
            "playlisttimelength",
            "panel",
            "panelrepeat",
            "panelplayorder",
            "panellength",
            "paneltimelength",
            "queue",
            "queueplayorder",
            "queuelength",
            "queuetimelength",
            "webradio",
            "webradiosourcecat",
            "webradiosource",
            "state",
            "mode",
            "volume",
        ]
        if self.hasVideoSupport():
            keys.extend([\
                "video",
                "videorepeat",
                "videoplayorder",
                "videolength",
                "videotimelength",
            ])
        known_modes = ("playlist", "panel", "dvd", "webradio", "video")
        for k in keys:
            self.assertTrue(k in ans.keys())
            if k == "mode":
                self.assertTrue(ans[k] in known_modes)
            elif k == "state":
                self.assertTrue(ans[k] in ('stop', 'play', 'pause'))

    def testGetServerInfo(self):
        """Test getServerInfo command"""
        ans = self.deejayd.get_server_info()
        keys = ('server_version', 'protocol_version')
        for k in keys:
            self.assertTrue(k in ans.keys())

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


        modes = ["playlist", "panel", "queue"]
        if self.hasVideoSupport(): modes.append("video")
        for mode in modes:
            order = self.testdata.getRandomElement(("inorder", "random", \
                    "onemedia"))
            self.assertAckCmd(self.deejayd.set_option(mode, "playorder", order))
            status = self.deejayd.get_status()
            self.assertEqual(status[mode + "playorder"], order)
            if mode != "queue":
                rpt = self.testdata.getRandomElement((False, True))
                self.assertAckCmd(self.deejayd.set_option(mode, "repeat", rpt))

    def testSetRating(self):
        """Test set_rating command"""
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

# vim: ts=4 sw=4 expandtab
