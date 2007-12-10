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

    def test_objanswer_mechanism(self):
        """Test the objanswer mechanism to disable DeejaydAnswer objects in returns parameters."""
        known_mode = 'playlist'

        # objanswer mechanism on (default)
        ans = self.deejayd.set_mode(known_mode)
        self.failUnless(ans.get_contents())
        ans = self.deejayd.get_status()
        self.assertEqual(ans.get_contents()['mode'], known_mode)

        # objanswer mechanism off
        ans = self.deejayd.set_mode(known_mode, objanswer=False)
        self.failUnless(ans == None)
        ans = self.deejayd.get_status(objanswer=False)
        self.assertEqual(ans['mode'], known_mode)


# vim: ts=4 sw=4 expandtab
