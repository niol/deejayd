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


# vim: ts=4 sw=4 expandtab
