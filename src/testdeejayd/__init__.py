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

import sys
import unittest
from testdeejayd.databuilder import TestData, TestAudioCollection,\
                                    TestVideoCollection
from testdeejayd.xmldatabuilder import DeejaydXMLSampleFactory


class DeejaydTest(unittest.TestCase):

    def setUp(self):
        from deejayd.ui.i18n import DeejaydTranslations
        t = DeejaydTranslations()
        t.install()


class TestCaseWithData(DeejaydTest):

    def setUp(self):
        super(TestCaseWithData, self).setUp()
        self.testdata = TestData()


class _TestCaseWithMediaData(DeejaydTest):

    def setUp(self):
        super(_TestCaseWithMediaData, self).setUp()
        self.testdata = self.collection_class()
        self.testdata.buildLibraryDirectoryTree()

    def tearDown(self):
        self.testdata.cleanLibraryDirectoryTree()


class TestCaseWithAudioData(_TestCaseWithMediaData):
    collection_class = TestAudioCollection


class TestCaseWithVideoData(_TestCaseWithMediaData):
    collection_class = TestVideoCollection


class TestCaseWithAudioAndVideoData(DeejaydTest):

    def setUp(self):
        super(TestCaseWithAudioAndVideoData, self).setUp()

        self.testdata = TestData()
        # audio library
        self.test_audiodata = TestAudioCollection()
        self.test_audiodata.buildLibraryDirectoryTree()

        # video library
        self.test_videodata = TestVideoCollection()
        self.test_videodata.buildLibraryDirectoryTree()

    def tearDown(self):
        self.test_audiodata.cleanLibraryDirectoryTree()
        self.test_videodata.cleanLibraryDirectoryTree()


class XmlTestCase(TestCaseWithData):

    def setUp(self):
        super(XmlTestCase, self).setUp()
        self.xmldata = DeejaydXMLSampleFactory()

    def assert_filter_matches_sample(self, retrieved_filter):
        self.assertEqual(retrieved_filter.__class__.__name__, 'And')
        anded = retrieved_filter.filterlist
        self.assertEqual(anded[0].__class__.__name__, 'Contains')
        self.assertEqual(anded[0].tag, 'artist')
        self.assertEqual(anded[0].pattern, 'Britney')
        self.assertEqual(anded[1].__class__.__name__, 'Or')
        ored = anded[1].filterlist
        self.assertEqual(ored[0].__class__.__name__, 'Equals')
        self.assertEqual(ored[0].tag, 'genre')
        self.assertEqual(ored[0].pattern, 'Classical')
        self.assertEqual(ored[1].__class__.__name__, 'Equals')
        self.assertEqual(ored[1].tag, 'genre')
        self.assertEqual(ored[1].pattern, 'Disco')


# vim: ts=4 sw=4 expandtab
