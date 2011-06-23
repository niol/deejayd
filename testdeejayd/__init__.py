# Deejayd, a media player daemon
# Copyright (C) 2007-2009 Mickael Royer <mickael.royer@gmail.com>
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

import sys, os, shutil
import unittest

from testdeejayd.databuilder import TestData, TestAudioCollection,\
                                    TestVideoCollection
from testdeejayd.server import TestServer
from deejayd.ui.config import DeejaydConfig


class DeejaydTest(unittest.TestCase):

    def setUp(self):
        from deejayd.ui.i18n import DeejaydTranslations
        t = DeejaydTranslations()
        t.install()


class TestCaseWithData(DeejaydTest):

    def setUp(self):
        super(TestCaseWithData, self).setUp()
        self.testdata = TestData()

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


class _TestCaseWithMediaData(DeejaydTest):

    def setUp(self):
        super(_TestCaseWithMediaData, self).setUp()
        self.testdata = self.collection_class()
        self.testdata.buildLibraryDirectoryTree()

    def tearDown(self):
        self.testdata.cleanLibraryDirectoryTree()


class TestCaseWithAudioData(_TestCaseWithMediaData):
    collection_class = TestAudioCollection


class TestCaseWithVideoData(_TestCaseWithMediaData):
    collection_class = TestVideoCollection


class TestCaseWithAudioAndVideoData(DeejaydTest):
    video_support = True

    def setUp(self):
        super(TestCaseWithAudioAndVideoData, self).setUp()

        self.testdata = TestData()
        # audio library
        self.test_audiodata = TestAudioCollection()
        self.test_audiodata.buildLibraryDirectoryTree()

        # video library
        self.test_videodata = TestVideoCollection()
        self.test_videodata.buildLibraryDirectoryTree()

    def tearDown(self):
        self.test_audiodata.cleanLibraryDirectoryTree()
        self.test_videodata.cleanLibraryDirectoryTree()


class TestCaseWithServer(TestCaseWithAudioAndVideoData):
    profiles = "default"

    def setUp(self):
        super(TestCaseWithServer, self).setUp()
        # create custom configuration files
        current_dir = os.path.dirname(__file__)
        DeejaydConfig.custom_conf = os.path.join(current_dir,\
                "profiles", self.profiles)
        config = DeejaydConfig(force_parse = True)
        config.set('mediadb', 'music_directory',\
                self.test_audiodata.getRootDir())
        config.set('mediadb', 'video_directory',\
                self.test_videodata.getRootDir())
        self.dbfilename = None
        if config.get('database', 'db_type') == 'sqlite':
            self.dbfilename = '/tmp/testdeejayddb-' +\
                    self.testdata.getRandomString() + '.db'
            config.set('database', 'db_name', self.dbfilename)
        elif config.get('database', 'db_type') == 'mysql':
            import MySQLdb
            try:
                connection = MySQLdb.connect(\
                    db=config.get('database', 'db_name'),\
                    user=config.get('database', 'db_user'),\
                    passwd=config.get('database', 'db_password'),\
                    host=config.get('database', 'db_host'),\
                    port=config.getint('database', 'db_port'),\
                    use_unicode=True, charset="utf8")
            except MySQLdb.DatabaseError:
                print "Unable to connect to mysql db"
                sys.exit(1)
            cursor = connection.cursor()
           # drop all table
            from deejayd.database.schema import db_schema
            for table in db_schema:
                try:
                    cursor.execute("DROP TABLE `%s`" % table.name)
                except MySQLdb.DatabaseError:
                    pass
           # commit changes and close
            connection.commit()
            connection.close()

        # disable all plugins for tests
        config.set('general', 'enabled_plugins', '')

        config.set('database', 'db_name', self.dbfilename)
        self.tmp_dir = None
        if config.getboolean("webui","enabled"):
            # define a tmp directory
            self.tmp_dir = '/tmp/testdeejayd-tmpdir-'+\
                    self.testdata.getRandomString()
            config.set("webui", "tmp_dir", self.tmp_dir)

        # record config to be used by the test server
        self.conf = os.path.join(current_dir, "profiles", "current")
        fp = open(self.conf, "w")
        config.write(fp)
        fp.close()
        os.chmod(self.conf, 0644)

        # launch server
        self.testserver = TestServer(self.conf)
        self.testserver.start()

        # record port for clients
        self.serverPort = config.getint('net', 'port')
        self.webServerPort = config.getint('webui', 'port')

        # update video_support var
        self.video_support = True

    def tearDown(self):
        self.testserver.stop()
        if self.dbfilename is not None: # Clean up temporary db file
            os.unlink(self.dbfilename)
        if self.tmp_dir is not None:
             try: shutil.rmtree(self.tmp_dir)
             except (IOError, OSError):
                 pass
        os.unlink(self.conf)
        super(TestCaseWithServer, self).tearDown()

# vim: ts=4 sw=4 expandtab
