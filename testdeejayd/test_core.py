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

import os

from twisted.internet import reactor
import kaa

from testdeejayd import TestCaseWithAudioAndVideoData
from testdeejayd.coreinterface import InterfaceTests, InterfaceSubscribeTests

from deejayd.core import DeejayDaemonCore
from deejayd.ui.config import DeejaydConfig


class TestCore(TestCaseWithAudioAndVideoData, InterfaceTests):
#                                              InterfaceSubscribeTests):
    """Test the deejayd daemon core."""

    def assertAckCmd(self, cmd_res):
        self.assertEqual(cmd_res, None)

    def setUp(self):
        TestCaseWithAudioAndVideoData.setUp(self)

        config = DeejaydConfig()
        self.dbfilename = '/tmp/testdeejayddb-' +\
                          self.testdata.getRandomString() + '.db'

        config.set('general', 'enabled_plugins', '')
        config.set('general','activated_modes','playlist,panel,webradio,video')
        config.set('database', 'db_type', 'sqlite')
        config.set('database', 'db_name', self.dbfilename)

        config.set('mediadb','music_directory',self.test_audiodata.getRootDir())
        config.set('mediadb','video_directory',self.test_videodata.getRootDir())

        # player option
        config.set('general','media_backend',"xine")
        config.set('general','video_support',"yes")
        config.set('xine','audio_output',"none")
        config.set('xine','video_output',"none")

        self.deejayd = DeejayDaemonCore(config)
        self.deejayd.audiolib._update()
        self.deejayd.videolib._update()

        self.is_running = True

    def tearDown(self):
        if self.is_running:
            self.deejayd.close()
            # be sure that all kaa thread are stopped
            kaa.main.stop()

        os.unlink(self.dbfilename)
        TestCaseWithAudioAndVideoData.tearDown(self)

    def test_sub_broadcast_mediadb_aupdate(self):
        """Checks that mediadb.aupdate signals are broadcasted."""
        # disable here because pyinotify threads are not launched


    def test_sub_broadcast_mediadb_vupdate(self):
        """Checks that mediadb.vupdate signals are broadcasted."""
        # disable here because pyinotify threads are not launched

# vim: ts=4 sw=4 expandtab
