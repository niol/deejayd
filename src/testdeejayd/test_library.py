# Deejayd, a media player daemon
# Copyright (C) 2007-2008 Mickael Royer <mickael.royer@gmail.com>
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
import os,time
from testdeejayd import TestCaseWithMediaData
from deejayd.database.sqlite import SqliteDatabase
from deejayd.mediadb.library import AudioLibrary, VideoLibrary, \
                                                            NotFoundException
from deejayd.mediadb import inotify

# FIXME : Those imports should really go away one day
from deejayd.player import xine
from deejayd.ui.config import DeejaydConfig


class TestDeejayDBLibrary(TestCaseWithMediaData):

    def tearDown(self):
        self.removeDB()
        TestCaseWithMediaData.tearDown(self)

    def setUpDB(self):
        self.dbfilename = '/tmp/testdeejayddb-' + \
            self.testdata.getRandomString()
        self.db = SqliteDatabase(self.dbfilename)
        self.db.connect()

        # init player
        config = DeejaydConfig()
        config.set('xine','audio_output',"none")
        config.set('xine','video_output',"none")
        player = xine.XinePlayer(self.db, config)
        player.init_video_support()

        self.library = self.__class__.library_class(self.db, player, \
                                                    self.testdata.getRootDir())

    def removeDB(self):
        self.db.close()
        os.remove(self.dbfilename)

    def verifyMediaDBContent(self, testTag = True, do_update = True):
        time.sleep(0.2)
        if do_update: # First update mediadb
            self.library._update()
        else:
            time.sleep(0.5)

        self.assertRaises(NotFoundException,
                  self.library.get_dir_content, self.testdata.getRandomString())
        self.assertRaises(NotFoundException,
                  self.library.get_file, self.testdata.getRandomString())

        for root, dirs, files in os.walk(self.testdata.getRootDir()):
            try: root = root.decode("utf-8", "strict").encode("utf-8")
            except UnicodeError:
                continue

            new_dirs = []
            for d in dirs:
                try: d = d.decode("utf-8", "strict").encode("utf-8")
                except UnicodeError:
                    continue
                new_dirs.append(d)
            dirs = new_dirs

            new_files = []
            for f in files:
                try: f = f.decode("utf-8", "strict").encode("utf-8")
                except UnicodeError:
                    continue
                new_files.append(f)
            files = new_files

            current_root = self.testdata.stripRoot(root)
            try: contents = self.library.get_dir_content(current_root)
            except NotFoundException:
                allContents = self.library.get_dir_content('')
                self.assert_(False,
                    "'%s' is in directory tree but was not found in DB %s" %\
                    (current_root,str(allContents)))

            # First, verify directory list
            self.assertEqual(len(contents["dirs"]), len(dirs))
            for dir in dirs:
                self.assert_(dir in contents["dirs"],
                    "'%s' is in directory tree but was not found in DB %s in current root '%s'" % (dir,str(contents["dirs"]),current_root))

            # then, verify file list
            self.assertEqual(len(contents["files"]), len(files))
            db_files = [f["path"] for f in contents["files"]]
            for file in files:
                (name,ext) = os.path.splitext(file)
                relPath = os.path.join(current_root, file)
                if ext.lower() in self.__class__.supported_ext:
                    self.assert_(relPath in db_files,
                    "'%s' is a file in directory tree but was not found in DB"\
                    % relPath)
                    if testTag: self.verifyTag(relPath)

    def verifyTag(self,filePath):
        try: inDBfile = self.library.get_file(filePath)
        except NotFoundException:
            self.assert_(False,
                "'%s' is a file in directory tree but was not found in DB"\
                % media.name)
        else: inDBfile = inDBfile[0]

        realFile = self.testdata.medias[filePath]

        return (inDBfile, realFile)


class TestVideoLibrary(TestDeejayDBLibrary):
    library_class = VideoLibrary
    supported_ext = (".mpg",".avi")

    def setUp(self):
        TestDeejayDBLibrary.setUp(self)
        self.testdata.build_video_library_directory_tree()
        self.setUpDB()
        self.library._update()

    def testGetDir(self):
        """built directory detected by video library"""
        self.verifyMediaDBContent()

    def testAddSubdirectory(self):
        """Add a subdirectory in video library"""
        self.testdata.addSubdir()
        self.verifyMediaDBContent()

    def testAddMedia(self):
        """Add a media file in video library"""
        self.testdata.addMedia()
        self.verifyMediaDBContent()

    def verifyTag(self, filePath):
        (inDBfile, realFile) = TestDeejayDBLibrary.verifyTag(self, filePath)

        for tag in ('length', 'videowidth', 'videoheight'):
            self.assertEqual(realFile[tag], inDBfile[tag])


class TestAudioLibrary(TestDeejayDBLibrary):
    library_class = AudioLibrary
    supported_ext = (".ogg",".mp3",".mp4")

    def setUp(self):
        TestDeejayDBLibrary.setUp(self)
        self.testdata.build_audio_library_directory_tree()
        self.setUpDB()
        self.library._update()

    def testGetDir(self):
        """built directory detected by audio library"""
        self.verifyMediaDBContent()

    def testAddDirectory(self):
        """Add a directory in audio library"""
        self.testdata.addDir()
        self.verifyMediaDBContent()

    def testAddSubdirectory(self):
        """Add a subdirectory in audio library"""
        self.testdata.addSubdir()
        self.verifyMediaDBContent()

    def testRenameDirectory(self):
        """Rename a directory in audio library"""
        self.testdata.renameDir()
        self.verifyMediaDBContent(False)

    def testRemoveDirectory(self):
        """Remove a directory in audio library"""
        self.testdata.removeDir()
        self.verifyMediaDBContent()

    def testAddMedia(self):
        """Add a media file in audio library"""
        self.testdata.addMedia()
        self.verifyMediaDBContent()

    def testRenameMedia(self):
        """Rename a media file in audio library"""
        self.testdata.renameMedia()
        self.verifyMediaDBContent(False)

    def testRemoveMedia(self):
        """Remove a media file in audio library"""
        self.testdata.removeMedia()
        self.verifyMediaDBContent()

    def testChangeTag(self):
        """Tag value change detected by audio library"""
        self.testdata.changeMediaTags()
        self.verifyMediaDBContent()

    def testSearchFile(self):
        """Search a file in audio library"""
        self.assertRaises(NotFoundException,
              self.library.search, self.testdata.getRandomString(),\
              self.testdata.getRandomString())

        self.assertEqual([],
                  self.library.search("genre", self.testdata.getRandomString()))

        medias = self.testdata.medias.keys()
        media = self.testdata.medias[medias[0]]
        self.assertEqual(1,len(self.library.search("genre", media["genre"])))

    def verifyTag(self,filePath):
        (inDBfile, realFile) = TestDeejayDBLibrary.verifyTag(self, filePath)

        for tag in ("title","artist","album","genre"):
            self.assert_(realFile[tag] == inDBfile[tag],
                "tag %s for %s different between DB and reality %s != %s" % \
                (tag,realFile["filename"],realFile[tag],inDBfile[tag]))


class TestInotifySupport(TestDeejayDBLibrary):
    library_class = AudioLibrary
    supported_ext = (".ogg",".mp3",".mp4")

    def setUp(self):
        TestDeejayDBLibrary.setUp(self)
        self.testdata.build_audio_library_directory_tree()
        self.setUpDB()

        # start inotify thread
        self.watcher = inotify.DeejaydInotify(self.db, self.library, None)
        self.watcher.start()

        self.library._update()

    def tearDown(self):
        self.watcher.close()
        TestDeejayDBLibrary.tearDown(self)

    def testAddMedia(self):
        """Inotify support : Add a media in audio library"""
        self.testdata.addMedia()
        self.verifyMediaDBContent(do_update = False)

    def testAddSubdirectory(self):
        """Inotify support : Add a subdirectory"""
        self.testdata.addSubdir()
        time.sleep(3)
        self.verifyMediaDBContent(do_update = False)

    def testRenameDirectory(self):
        """Inotify support : Rename a directory"""
        self.testdata.renameDir()
        self.verifyMediaDBContent(False, do_update = False)

    def testRemoveDirectory(self):
        """Inotify support : Remove a directory"""
        self.testdata.removeDir()
        self.verifyMediaDBContent(do_update = False)

    def testChangeTag(self):
        """Inotify support : Tag value change detected"""
        self.testdata.changeMediaTags()
        self.verifyMediaDBContent(do_update = False)

    def verifyTag(self,filePath):
        (inDBfile, realFile) = TestDeejayDBLibrary.verifyTag(self, filePath)

        for tag in ("title","artist","album","genre"):
            self.assert_(realFile[tag] == inDBfile[tag],
                "tag %s for %s different between DB and reality %s != %s" % \
                (tag,realFile["filename"],realFile[tag],inDBfile[tag]))

# vim: ts=4 sw=4 expandtab
