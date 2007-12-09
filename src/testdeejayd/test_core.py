import os

from testdeejayd import TestCaseWithMediaData
from testdeejayd.coreinterface import InterfaceTests

from deejayd.core import DeejayDaemonCore
from deejayd.ui.config import DeejaydConfig


class TestCore(TestCaseWithMediaData, InterfaceTests):
    """Test the deejayd daemon core."""

    def setUp(self):
        TestCaseWithMediaData.setUp(self)
        self.testdata.build_audio_library_directory_tree()

        config = DeejaydConfig()
        self.dbfilename = '/tmp/testdeejayddb-' +\
                          self.testdata.getRandomString() + '.db'
        config.set('database', 'db_file', self.dbfilename)

        config.set('mediadb', 'music_directory', self.testdata.getRootDir())
        config.set('mediadb', 'video_directory', self.testdata.getRootDir())

        self.deejayd = DeejayDaemonCore(config)
        self.deejayd.audio_library._update()

    def tearDown(self):
        os.unlink(self.dbfilename)
        TestCaseWithMediaData.tearDown(self)


# vim: ts=4 sw=4 expandtab
