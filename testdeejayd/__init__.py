import unittest
from testdeejayd.databuilder import TestMusicCollection,TestCommand
import testdeejayd.data

class TestCaseWithData(unittest.TestCase):

    def setUp(self):
        self.testdata = TestMusicCollection(testdeejayd.data.songlibrary)


class TestCaseWithFileData(TestCaseWithData):

    def setUp(self):
        TestCaseWithData.setUp(self)
        self.testdata.buildLibraryDirectoryTree('/tmp')

    def tearDown(self):
        self.testdata.cleanLibraryDirectoryTree()


class TestCaseWithCommand(unittest.TestCase):

    def setUp(self):
        self.testcmd = TestCommand

# vim: ts=4 sw=4 expandtab
