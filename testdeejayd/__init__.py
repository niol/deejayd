import sys
import unittest
from testdeejayd.databuilder import TestData, TestMusicCollection, TestProvidedMusicCollection, TestCommand

class TestCaseWithData(unittest.TestCase):

    def setUp(self):
        self.testdata = TestData()


class TestCaseWithFileData(TestCaseWithData):

    def setUp(self):
        TestCaseWithData.setUp(self)
        self.testdata.buildLibraryDirectoryTree('/tmp')

    def tearDown(self):
        self.testdata.cleanLibraryDirectoryTree()


class TestCaseWithCommand(unittest.TestCase):

    def setUp(self):
        self.testcmd = TestCommand


class TestCaseWithProvidedMusic(unittest.TestCase):

    def setUp(self):
        self.testdata = TestProvidedMusicCollection(sys.argv[1])


# vim: ts=4 sw=4 expandtab
