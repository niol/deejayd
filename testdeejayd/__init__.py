# Deejayd, a media player daemon
# Copyright (C) 2007-2017 Mickael Royer <mickael.royer@gmail.com>
#                         Alexandre Rossi <alexandre.rossi@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os
import shutil
from testdeejayd.utils.databuilder import TestData, TestAudioCollection
from testdeejayd.utils.databuilder import TestVideoCollection
import testdeejayd.utils.twreactor
from testdeejayd.utils.server import TestServer
from deejayd.ui.config import DeejaydConfig
from deejayd.db import connection
import unittest


class _DeejaydTest(unittest.TestCase):
    media_backend = "vlc"
    dbfilename = None

    @classmethod
    def setUpClass(cls):
        cls.testdata = TestData()

        # load translation files
        from deejayd.ui.i18n import DeejaydTranslations
        t = DeejaydTranslations()
        t.install()

        # prepare config object
        custom_conf = os.path.join(os.path.dirname(__file__), 
                                   "utils", "defaults.conf")
        cls.config = DeejaydConfig()
        cls.config.read([custom_conf])
        cls.config.set("general", "media_backend", cls.media_backend)

        rnd_str = cls.testdata.get_random_string()
        cls.dbfilename = '/tmp/testdeejayddb-' + rnd_str + '.db'
        cls.config.set('database', 'uri', "sqlite:///"+cls.dbfilename)

        # disable all plugins for tests
        cls.config.set('general', 'enabled_plugins', '')

        # disable icecast, not supported in test
        cls.config.set('webradio', 'icecast', 'no')

    @classmethod
    def tearDownClass(cls):
        if cls.dbfilename is not None:
            try:
                os.unlink(cls.dbfilename)
            except (OSError, IOError):
                pass
            cls.dbfilename = None
        cls.config.destroy()

    def hasVideoSupport(self):
        return self.config.getboolean("video", "enabled")


class TestCaseWithData(_DeejaydTest):

    def assert_filter_matches_sample(self, retrieved_filter):
        self.assertEqual(retrieved_filter.__class__.__name__, 'And')
        anded = retrieved_filter.filterlist
        self.assertEqual(anded[0].__class__.__name__, 'Contains')
        self.assertEqual(anded[0].tag, 'artist')
        self.assertEqual(anded[0].pattern, 'Britney')
        self.assertEqual(anded[1].__class__.__name__, 'Or')
        ored = anded[1].filterlist
        self.assertEqual(ored[0].__class__.__name__, 'Equals')
        self.assertEqual(ored[0].tag, 'genre')
        self.assertEqual(ored[0].pattern, 'Classical')
        self.assertEqual(ored[1].__class__.__name__, 'Equals')
        self.assertEqual(ored[1].tag, 'genre')
        self.assertEqual(ored[1].pattern, 'Disco')


class TestCaseWithMediaData(_DeejaydTest):

    @classmethod
    def setUpClass(cls):
        super(TestCaseWithMediaData, cls).setUpClass()

        # audio library
        cls.test_audiodata = TestAudioCollection()
        cls.test_audiodata.build()
        cls.config.set('mediadb', 'music_directory',
                       cls.test_audiodata.get_root_dir())

        # video library
        cls.test_videodata = TestVideoCollection()
        cls.test_videodata.build()
        cls.config.set('mediadb', 'video_directory',
                       cls.test_videodata.get_root_dir())

    @classmethod
    def tearDownClass(cls):
        cls.test_audiodata.clean()
        cls.test_videodata.clean()

        super(TestCaseWithMediaData, cls).tearDownClass()


class TestCaseWithDeejaydCore(TestCaseWithMediaData):
    inotify_support = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseWithDeejaydCore, cls).setUpClass()
        if cls.inotify_support or cls.media_backend == "gstreamer":
            testdeejayd.utils.twreactor.need_twisted_reactor()

        # configure database connection
        uri = DeejaydConfig().get("database", "uri")
        connection.init(uri)

        # init deejayd core
        from deejayd.server.core import DeejayDaemonCore
        cls.deejayd = DeejayDaemonCore(start_inotify=cls.inotify_support,
                                       library_update=False)
        cls.deejayd.audiolib.update(sync=True)
        cls.deejayd.videolib.update(sync=True)
        cls.is_running = True
        connection.Session.remove()

    @classmethod
    def tearDownClass(cls):
        if testdeejayd.utils.twreactor.TWISTED_REACTOR:
            testdeejayd.utils.twreactor.stop_twisted_reactor()
        if cls.is_running:
            cls.deejayd.close()
        super(TestCaseWithDeejaydCore, cls).tearDownClass()


class TestCaseWithServer(TestCaseWithMediaData):
    conf_file = None

    @classmethod
    def setUpClass(cls):
        super(TestCaseWithServer, cls).setUpClass()

        # record port for clients
        cls.serverPort = cls.config.getint('net', 'port')
        cls.webServerPort = cls.config.getint('webui', 'port')

        # define a tmp directory for webui
        cls.tmp_dir = '/tmp/testdeejayd-tmpdir-' \
                      + cls.testdata.get_random_string()
        cls.config.set("webui", "tmp_dir", cls.tmp_dir)

        # record config to be used by the test server
        cls.conf_file = "/tmp/testdeejayd-server-conf-" + \
                        cls.testdata.get_random_string()
        fp = open(cls.conf_file, "w")
        cls.config.write(fp)
        fp.close()
        os.chmod(cls.conf_file, 0o644)

        # launch server
        cls.testserver = TestServer(cls.conf_file)
        cls.testserver.start()

    @classmethod
    def tearDownClass(cls):
        cls.testserver.stop()

        try:
            shutil.rmtree(cls.tmp_dir)
        except (IOError, OSError):
            pass
        os.unlink(cls.conf_file)
        super(TestCaseWithServer, cls).tearDownClass()
