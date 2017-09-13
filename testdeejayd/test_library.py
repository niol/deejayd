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

"""
Deejayd DB testing module
"""
import os
import time
from deejayd import DeejaydError
from deejayd.library.audio import AudioLibrary
from deejayd.library.video import VideoLibrary
from testdeejayd import TestCaseWithDeejaydCore, unittest
from testdeejayd import TestData, TestAudioCollection
from testdeejayd import TestVideoCollection
#from deejayd.mediadb import inotify
inotify = False


#####################################
#                                   #
# Verification functions            #
#                                   #
#####################################
class _VerifyDeejayLibrary(object):
    SUPPORTED_EXT = []
    TESTED_TAGS = []
    inotify_support = False

    def verify_content(self, test_tag=True):
        if not self.inotify_support:
            self.library.update(sync=True)
        else:
            time.sleep(1)

        self.assertRaises(DeejaydError,
                          self.library.get_dir_content, 
                          self.testdata.get_random_string())
        self.__verify_root(self.collection.get_root_dir(), test_tag)

    def __verify_root(self, requested_root, test_tag=True, inlink_path=None):
        for root, dirs, files in os.walk(requested_root):
            try:
                root = root.decode("utf-8", "strict").encode("utf-8")
            except UnicodeError:
                continue
            strip_root = self.collection.strip_root(root)

            new_dirs = []
            for d in dirs:
                try:
                    d = d.decode("utf-8", "strict").encode("utf-8")
                except UnicodeError:
                    continue
                dir_path = os.path.join(root, d)
                if os.path.islink(dir_path):
                    rel_path = os.path.join(strip_root, d)
                    self.__verify_root(dir_path, test_tag, rel_path)
                new_dirs.append(d)
            dirs = new_dirs

            new_files = []
            for f in files:
                try:
                    f = f.decode("utf-8", "strict").encode("utf-8")
                except UnicodeError:
                    continue
                if f != "cover.jpg" and not f.endswith(".srt"):
                    new_files.append(f)
            files = new_files

            try:
                contents = self.library.get_dir_content(strip_root)
            except DeejaydError:
                all_contents = self.library.get_dir_content('')
                self.assertTrue(False,
                                "'%s' is in directory tree but was not found"
                                " in DB %s" % (root, str(all_contents)))

            # First, verify directory list
            self.assertEqual(contents["directories"].sort(), dirs.sort(),
                             "Directory list is different for %s" % root)

            # then, verify file list
            self.assertEqual(len(contents["files"]), len(files),
                             "Files list different for folder %s : %s != %s"
                             % (root,
                                [fl["filename"] for fl in contents["files"]], 
                                files))
            db_files = [fl["filename"] for fl in contents["files"]]
            for file in files:
                (name, ext) = os.path.splitext(file)
                if ext.lower() in self.SUPPORTED_EXT:
                    self.assertTrue(file in db_files,
                                    "'%s' is a file in directory tree but was"
                                    " not found in DB" % file)
                    rel_path = os.path.join(strip_root, file)
                    if test_tag:
                        self.verify_tag(rel_path, inlink_path)

    def verify_tag(self, file_path, inlink_path=None):
        try:
            db_file = self.library.get_file(file_path).to_json()
        except DeejaydError:
            self.assertTrue(False,
                            "'%s' is a file in directory tree but was not "
                            "found in DB" % file_path)

        if inlink_path:
            link_full_path = os.path.join(self.testdata.get_root_dir(),
                                          inlink_path)
            abs_path = file_path[len(inlink_path) + 1:]
            real_file = self.testdata.dirlinks[link_full_path].medias[abs_path]
        else:
            real_file = self.collection.get_media(file_path)

        for tag in self.TESTED_TAGS:
            self.assertTrue(unicode(real_file[tag]) == unicode(db_file[tag]),
                            "tag %s for %s different between DB and reality %s"
                            " != %s" % (tag, real_file["filename"], 
                                        real_file[tag], db_file[tag]))

        return real_file, db_file


class VerifyDeejayAudioLibrary(_VerifyDeejayLibrary):
    library_type = "audio"
    SUPPORTED_EXT = (".ogg", ".mp3", ".mp4", ".flac")
    TESTED_TAGS = ("title", "artist", "album", "genre")

    def verify_tag(self, file_path, inlink_path=None):
        (real_file, db_file) = super(VerifyDeejayAudioLibrary, self)\
                                .verify_tag(file_path, inlink_path)
        # verify cover attribute
        db_cover = self.library.get_cover(db_file["album_id"])
        dirname = os.path.dirname(real_file.get_path())
        cover_path = os.path.join(dirname, "cover.jpg")
        if os.path.isfile(cover_path):
            with open(cover_path) as fd:
                cover = fd.read()

            if db_cover is None:
                self.assertTrue(False, "cover %s exists but not "
                                "found in db" % cover_path)
            self.assertEqual(cover, db_cover["data"])
        else:
            if db_cover is not None:
                self.assertTrue(False, "cover for %s exists in DB but not "
                                       "in the real library" % file_path)


class VerifyDeejayVideoLibrary(_VerifyDeejayLibrary):
    library_type = "video"
    SUPPORTED_EXT = (".mpg", ".avi")
    TESTED_TAGS = ('length', 'width', 'height', 'external_subtitle')


#####################################
#                                   #
# test functions                    #
#                                   #
#####################################
class _TestDeejayLibrary(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.testdata = TestData()
        # load translation files
        from deejayd.ui.i18n import DeejaydTranslations
        t = DeejaydTranslations()
        t.install()
        # init database
        from deejayd.db import connection
        connection.init("sqlite://")

    @classmethod
    def tearDownClass(cls):
        cls.library.close()

    @unittest.skip("dirlinks test not work for now")
    def testDirlinks(self):
        self.collection.add_dir_link()
        self.verify_content()

        self.collection.move_dir_link()
        self.verify_content()

        self.collection.remove_dir_link()
        self.verify_content()

    def testGetDir(self):
        """built directory detected by library"""
        self.verify_content()

    def testAddSubdirectory(self):
        """Add a subdirectory in library"""
        self.collection.add_subdir()
        self.verify_content()

    def testRenameDirectory(self):
        """Rename a directory in library"""
        self.collection.rename_dir()
        self.verify_content(False)

    def testRemoveDirectory(self):
        """Remove a directory in library"""
        self.collection.remove_dir()
        self.verify_content()

    def testAddMedia(self):
        """Add a media file in library"""
        self.collection.add_media()
        self.verify_content()

    def testRenameMedia(self):
        """Rename a media file in library"""
        self.collection.rename_media()
        self.verify_content(False)

    def testRemoveMedia(self):
        """Remove a media file in library"""
        self.collection.remove_media()
        self.verify_content()


class TestAudioLibrary(_TestDeejayLibrary, VerifyDeejayAudioLibrary):

    @classmethod
    def setUpClass(cls):
        super(TestAudioLibrary, cls).setUpClass()
        cls.collection = TestAudioCollection()
        cls.collection.build()
        cls.library = AudioLibrary(cls.collection.get_root_dir())
        cls.library.update(sync=True)

    @classmethod
    def tearDownClass(cls):
        super(TestAudioLibrary, cls).tearDownClass()
        cls.collection.clean()

    def testChangeTag(self):
        """Tag value change detected by audio library"""
        self.collection.change_media_tags()
        self.verify_content()

    def testAddCover(self):
        """Add cover in audio library"""
        self.collection.add_cover()
        self.verify_content()

    def testRemoveCover(self):
        """Remove cover in audio library"""
        self.collection.remove_cover()
        self.verify_content()


class TestVideoLibrary(_TestDeejayLibrary, VerifyDeejayVideoLibrary):

    @classmethod
    def setUpClass(cls):
        super(TestVideoLibrary, cls).setUpClass()
        cls.collection = TestVideoCollection()
        cls.collection.build()
        cls.library = VideoLibrary(cls.collection.get_root_dir())
        cls.library.update(sync=True)

    @classmethod
    def tearDownClass(cls):
        super(TestVideoLibrary, cls).tearDownClass()
        cls.collection.clean()

    def testAddSubtitle(self):
        """Add a subtitle file in library"""
        self.collection.add_subtitle()
        self.verify_content()

    def testRemoveSubtitle(self):
        """Remove a subtitle file in library"""
        self.collection.remove_subtitle()
        self.verify_content()


#####################################
#                                   #
# test inotify functions            #
#                                   #
#####################################
class _TestInotifyDeejayLibrary(object):

    @unittest.skipIf(inotify is False, "inotify is not supported")
    def testInotifyAddMedia(self):
        """Inotify support : Add a media in audio library"""
        self.testdata.addMedia()
        self.verifyMediaDBContent()

    @unittest.skipIf(inotify is False, "inotify is not supported")
    def testInotifyAddSubdirectory(self):
        """Inotify support : Add a subdirectory"""
        self.testdata.addSubdir()
        self.verifyMediaDBContent()

    @unittest.skipIf(inotify is False, "inotify is not supported")
    def testInotifyRenameDirectory(self):
        """Inotify support : Rename a directory"""
        self.testdata.renameDir()
        self.verifyMediaDBContent(False)

    @unittest.skipIf(inotify is False, "inotify is not supported")
    def testInotifyRemoveDirectory(self):
        """Inotify support : Remove a directory"""
        self.testdata.removeDir()
        self.verifyMediaDBContent()


class TestInotifyVideoLibrary(TestCaseWithDeejaydCore, \
        _TestInotifyDeejayLibrary, VerifyDeejayVideoLibrary):
    inotify_support = True

    @classmethod
    def setUpClass(cls):
        super(TestInotifyVideoLibrary, cls).setUpClass()
        cls.library = getattr(cls.deejayd, cls.library_type + "lib")
        cls.testdata = getattr(cls, "test_" + cls.library_type + "data")

    @classmethod
    def tearDownClass(cls):
        super(TestInotifyVideoLibrary, cls).tearDownClass()

    def tearDown(self):
        self.library.update(sync=True)

    @unittest.skipIf(inotify is False, "inotify is not supported")
    def testInotifyAddSubtitle(self):
        """Inotify support : add subtitle detected"""
        self.testdata.add_subtitle()
        self.verifyMediaDBContent()

    @unittest.skipIf(inotify is False, "inotify is not supported")
    def testInotifyRemoveSubtitle(self):
        """Inotify support : remove subtitle detected"""
        self.testdata.remove_subtitle()
        self.verifyMediaDBContent()


class TestInotifyAudioLibrary(TestCaseWithDeejaydCore, \
        _TestInotifyDeejayLibrary, VerifyDeejayAudioLibrary):
    inotify_support = True

    @classmethod
    def setUpClass(cls):
        super(TestInotifyAudioLibrary, cls).setUpClass()
        cls.library = getattr(cls.deejayd, cls.library_type + "lib")
        cls.testdata = getattr(cls, "test_" + cls.library_type + "data")

    @classmethod
    def tearDownClass(cls):
        super(TestInotifyAudioLibrary, cls).tearDownClass()

    def tearDown(self):
        self.library.update(sync=True)

    @unittest.skipIf(inotify is False, "inotify is not supported")
    def testInotifyAddCover(self):
        """Inotify support : add cover detected"""
        self.testdata.add_cover()
        self.verifyMediaDBContent()

    @unittest.skipIf(inotify is False, "inotify is not supported")
    def testInotifyRemoveCover(self):
        """Inotify support : remove cover detected"""
        self.testdata.remove_cover()
        self.verifyMediaDBContent()

    @unittest.skipIf(inotify is False, "inotify is not supported")
    def testInotifyChangeTag(self):
        """Inotify support : Tag value change detected"""
        self.testdata.changeMediaTags()
        self.verifyMediaDBContent()

# vim: ts=4 sw=4 expandtab
