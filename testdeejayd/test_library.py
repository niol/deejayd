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
import os, time, traceback
from testdeejayd import TestCaseWithDeejaydCore, unittest
from deejayd.utils import str_decode
from deejayd.mediadb import inotify
from deejayd.mediadb.library import NotFoundException


#####################################
#                                   #
# Verification functions            #
#                                   #
#####################################
class _VerifyDeejayLibrary(object):
    tested_tags = []

    def verifyMediaDBContent(self, testTag=True):
        if not self.inotify_support:
            self.library.update(sync=True)
        else:
            time.sleep(1)

        self.assertRaises(NotFoundException,
                  self.library.get_dir_content, self.testdata.getRandomString())
        self.assertRaises(NotFoundException,
                  self.library.get_file, self.testdata.getRandomString())

        self.__verifyRoot(self.testdata.getRootDir(), testTag)

    def __verifyRoot(self, requested_root, testTag=True, inlink_path=None):
        for root, dirs, files in os.walk(requested_root):
            try: root = root.decode("utf-8", "strict").encode("utf-8")
            except UnicodeError:
                continue
            strip_root = self.testdata.stripRoot(root)

            new_dirs = []
            for d in dirs:
                try: d = d.decode("utf-8", "strict").encode("utf-8")
                except UnicodeError:
                    continue
                dir_path = os.path.join(root, d)
                if os.path.islink(dir_path):
                    rel_path = os.path.join(strip_root, d)
                    self.__verifyRoot(dir_path, testTag, rel_path)
                new_dirs.append(d)
            dirs = new_dirs

            new_files = []
            for f in files:
                try: f = f.decode("utf-8", "strict").encode("utf-8")
                except UnicodeError:
                    continue
                if f != "cover.jpg" and not f.endswith(".srt"):
                    new_files.append(f)
            files = new_files

            try: contents = self.library.get_dir_content(strip_root)
            except NotFoundException:
                allContents = self.library.get_dir_content('')
                self.assertTrue(False,
                    "'%s' is in directory tree but was not found in DB %s" % \
                    (root, str(allContents)))

            # First, verify directory list
            self.assertEqual(contents["directories"].sort(), dirs.sort(),
                             "Directory list is different for folder %s" % root)

            # then, verify file list
            self.assertEqual(len(contents["files"]), len(files),
                    "Files list different for folder %s : %s != %s"\
                    % (root, [f["filename"] for f in contents["files"]], files))
            db_files = [f["filename"] for f in contents["files"]]
            for file in files:
                (name, ext) = os.path.splitext(file)
                if ext.lower() in self.__class__.supported_ext:
                    self.assertTrue(file in db_files,
                    "'%s' is a file in directory tree but was not found in DB"\
                    % file)
                    relPath = os.path.join(strip_root, file)
                    if testTag:
                        self.verifyTag(relPath, inlink_path)

    def verifyTag(self, filePath, inlink_path=None):
        try: inDBfile = self.library.get_file(filePath)
        except NotFoundException:
            self.assertTrue(False,
                "'%s' is a file in directory tree but was not found in DB"\
                % filePath)
        inDBfile = inDBfile[0]

        if inlink_path:
            link_full_path = os.path.join(self.testdata.getRootDir(),
                                          inlink_path)
            abs_path = filePath[len(inlink_path) + 1:]
            realFile = self.testdata.dirlinks[link_full_path].medias[abs_path]
        else:
            realFile = self.testdata.getMedia(filePath)

        for tag in self.tested_tags:
            self.assert_(realFile[tag] == inDBfile[tag],
                "tag %s for %s different between DB and reality %s != %s" % \
                (tag, realFile["filename"], realFile[tag], inDBfile[tag]))

        return (realFile, inDBfile)

class VerifyDeejayAudioLibrary(_VerifyDeejayLibrary):
    library_type = "audio"
    supported_ext = (".ogg", ".mp3", ".mp4", ".flac")
    tested_tags = ("title", "artist", "album", "genre")

    def verifyTag(self, filePath, inlink_path=None):
        (realFile, inDBfile) = super(VerifyDeejayAudioLibrary, self)\
                                            .verifyTag(filePath, inlink_path)
        # verify cover attribute
        dirname = os.path.dirname(realFile.get_path())
        cover_path = os.path.join(dirname, "cover.jpg")
        if os.path.isfile(cover_path):
            try: fd = open(cover_path)
            except Exception:
                self.assertTrue(False, \
                    "Cover %s exists but we don't succeed to open it" \
                    % cover_path)
                print "------------------Traceback lines--------------------"
                print str_decode(traceback.format_exc(), errors='replace')
                print "-----------------------------------------------------"
                return
            cover = fd.read()
            fd.close()

            try: inDBCover = self.library.get_cover(inDBfile["media_id"])
            except NotFoundException:
                self.assertTrue(False, "cover %s exists but not found in db"\
                                % cover_path)
            self.assertEqual(cover, inDBCover["cover"])

class VerifyDeejayVideoLibrary(_VerifyDeejayLibrary):
    library_type = "video"
    supported_ext = (".mpg", ".avi")
    tested_tags = ('length', 'videowidth', 'videoheight', 'external_subtitle')


#####################################
#                                   #
# test functions                    #
#                                   #
#####################################
class _TestDeejayLibrary(object):

    @unittest.skip("dirlinks test not work for now")
    def testDirlinks(self):
        self.testdata.addDirLink()
        self.verifyMediaDBContent()

        self.testdata.moveDirLink()
        self.verifyMediaDBContent()

        self.testdata.removeDirLink()
        self.verifyMediaDBContent()

    def testGetDir(self):
        """built directory detected by library"""
        self.verifyMediaDBContent()

    def testAddSubdirectory(self):
        """Add a subdirectory in library"""
        self.testdata.addSubdir()
        self.verifyMediaDBContent()

    def testRenameDirectory(self):
        """Rename a directory in library"""
        self.testdata.renameDir()
        self.verifyMediaDBContent(False)

    def testRemoveDirectory(self):
        """Remove a directory in library"""
        self.testdata.removeDir()
        self.verifyMediaDBContent()

    def testAddMedia(self):
        """Add a media file in library"""
        self.testdata.addMedia()
        self.verifyMediaDBContent()

    def testRenameMedia(self):
        """Rename a media file in library"""
        self.testdata.renameMedia()
        self.verifyMediaDBContent(False)

    def testRemoveMedia(self):
        """Remove a media file in library"""
        self.testdata.removeMedia()
        self.verifyMediaDBContent()


class TestAudioLibrary(TestCaseWithDeejaydCore, \
        _TestDeejayLibrary, VerifyDeejayAudioLibrary):

    @classmethod
    def setUpClass(cls):
        super(TestAudioLibrary, cls).setUpClass()
        cls.library = getattr(cls.deejayd, cls.library_type + "lib")
        cls.testdata = getattr(cls, "test_" + cls.library_type + "data")

    def testChangeTag(self):
        """Tag value change detected by audio library"""
        self.testdata.changeMediaTags()
        self.verifyMediaDBContent()

    def testAddCover(self):
        """Add cover in audio library"""
        self.testdata.add_cover()
        self.verifyMediaDBContent()

    def testRemoveCover(self):
        """Add cover in audio library"""
        self.testdata.remove_cover()
        self.verifyMediaDBContent()


class TestVideoLibrary(TestCaseWithDeejaydCore, \
        _TestDeejayLibrary, VerifyDeejayVideoLibrary):

    @classmethod
    def setUpClass(cls):
        super(TestVideoLibrary, cls).setUpClass()
        cls.library = getattr(cls.deejayd, cls.library_type + "lib")
        cls.testdata = getattr(cls, "test_" + cls.library_type + "data")

    def testAddSubtitle(self):
        """Add a subtitle file in library"""
        self.testdata.add_subtitle()
        self.verifyMediaDBContent()

    def testRemoveSubtitle(self):
        """Remove a subtitle file in library"""
        self.testdata.remove_subtitle()
        self.verifyMediaDBContent()

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
