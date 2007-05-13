import sys
import unittest
from testdeejayd.databuilder import TestData, TestMediaCollection, TestProvidedMusicCollection


class TestCaseWithData(unittest.TestCase):

    def setUp(self):
        self.testdata = TestData()


class TestCaseWithMediaData(unittest.TestCase):

    def setUp(self):
        self.testdata = TestMediaCollection()
        self.testdata.buildMusicDirectoryTree()

    def tearDown(self):
        self.testdata.cleanLibraryDirectoryTree()


class TestCaseWithProvidedMusic(unittest.TestCase):

    def setUp(self):
        self.testdata = TestProvidedMusicCollection(sys.argv[1])


# vim: ts=4 sw=4 expandtab
