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

import sys
import unittest
from testdeejayd.databuilder import TestData, TestMediaCollection


class TestCaseWithData(unittest.TestCase):

    def setUp(self):
        self.testdata = TestData()


class TestCaseWithMediaData(unittest.TestCase):

    def setUp(self):
        self.testdata = TestMediaCollection()

    def tearDown(self):
        self.testdata.cleanLibraryDirectoryTree()


class TestCaseWithAudioAndVideoData(unittest.TestCase):

    def setUp(self):
        self.testdata = TestData()
        # audio library
        self.test_audiodata = TestMediaCollection()
        self.test_audiodata.build_audio_library_directory_tree()

        # video library
        self.test_videodata = TestMediaCollection()
        self.test_videodata.build_video_library_directory_tree()

    def tearDown(self):
        self.test_audiodata.cleanLibraryDirectoryTree()
        self.test_videodata.cleanLibraryDirectoryTree()

# vim: ts=4 sw=4 expandtab
