import sys
import unittest
from testdeejayd.databuilder import TestData, TestAudioCollection, \
                TestVideoCollection, TestProvidedMusicCollection


class TestCaseWithData(unittest.TestCase):

    def setUp(self):
        self.testdata = TestData()


class TestCaseWithAudioData(unittest.TestCase):

    def setUp(self):
        self.testdata = TestAudioCollection()
        self.testdata.buildLibraryDirectoryTree()

    def tearDown(self):
        self.testdata.cleanLibraryDirectoryTree()


class TestCaseWithVideoData(TestCaseWithAudioData):

    def setUp(self):
        self.testdata = TestVideoCollection()
        self.testdata.buildLibraryDirectoryTree()


class TestCaseWithProvidedMusic(unittest.TestCase):

    def setUp(self):
        self.testdata = TestProvidedMusicCollection(sys.argv[1])


# vim: ts=4 sw=4 expandtab
