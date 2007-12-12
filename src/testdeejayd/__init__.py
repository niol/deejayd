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
