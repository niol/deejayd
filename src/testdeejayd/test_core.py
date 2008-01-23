# Deejayd, a media player daemon
# Copyright (C) 2007 Mickael Royer <mickael.royer@gmail.com>
#                    Alexandre Rossi <alexandre.rossi@gmail.com>
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

import os

from testdeejayd import TestCaseWithAudioAndVideoData
from testdeejayd.coreinterface import InterfaceTests, InterfaceSubscribeTests

from deejayd.core import DeejayDaemonCore
from deejayd.ui.config import DeejaydConfig


class TestCore(TestCaseWithAudioAndVideoData, InterfaceTests,
                                              InterfaceSubscribeTests):
    """Test the deejayd daemon core."""

    def setUp(self):
        TestCaseWithAudioAndVideoData.setUp(self)

        config = DeejaydConfig()
        self.dbfilename = '/tmp/testdeejayddb-' +\
                          self.testdata.getRandomString() + '.db'
        config.set('database', 'db_file', self.dbfilename)

        config.set('mediadb','music_directory',self.test_audiodata.getRootDir())
        config.set('mediadb','video_directory',self.test_videodata.getRootDir())

        # player option
        config.set('general','media_backend',"xine")
        config.set('general','video_support',"yes")
        config.set('xine','audio_output',"none")
        config.set('xine','video_output',"none")

        self.deejayd = DeejayDaemonCore(config)
        self.deejayd.audio_library._update()
        self.deejayd.video_library._update()

    def tearDown(self):
        self.deejayd.close()
        os.unlink(self.dbfilename)
        TestCaseWithAudioAndVideoData.tearDown(self)

    def test_objanswer_mechanism(self):
        """Test the objanswer mechanism to disable DeejaydAnswer objects in returns parameters."""
        known_mode = 'playlist'

        # objanswer mechanism on (default)
        ans = self.deejayd.set_mode(known_mode)
        self.failUnless(ans.get_contents())
        ans = self.deejayd.get_status()
        self.assertEqual(ans.get_contents()['mode'], known_mode)

        # objanswer mechanism off
        ans = self.deejayd.set_mode(known_mode, objanswer=False)
        self.failUnless(ans == None)
        ans = self.deejayd.get_status(objanswer=False)
        self.assertEqual(ans['mode'], known_mode)


# vim: ts=4 sw=4 expandtab
