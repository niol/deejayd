import unittest
from testdeejayd.databuilder import TestMusicCollection
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


# vim: ts=4 sw=4 expandtab
