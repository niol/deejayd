import sys
import unittest
from testdeejayd.databuilder import TestData, TestMusicCollection, TestProvidedMusicCollection, TestCommand

class TestCaseWithData(unittest.TestCase):

    def setUp(self):
        self.testdata = TestData()


class TestCaseWithFileData(TestCaseWithData):

    def setUp(self):
        TestCaseWithData.setUp(self)
        # FIXME Data should be generated
        # For the mean time, we use a cmdline passed music directory
        # self.testdata.buildLibraryDirectoryTree('/tmp')

    def tearDown(self):
        # FIXME Data is not generated yet, so we do not need to clean it
        # self.testdata.cleanLibraryDirectoryTree()
        pass


class TestCaseWithCommand(unittest.TestCase):

    def setUp(self):
        self.testcmd = TestCommand


class TestCaseWithProvidedMusic(unittest.TestCase):

    def setUp(self):
        self.testdata = TestProvidedMusicCollection(sys.argv[1])


# vim: ts=4 sw=4 expandtab
