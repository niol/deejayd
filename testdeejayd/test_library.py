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
import os,time
from testdeejayd import TestCaseWithAudioData, TestCaseWithVideoData
from deejayd import database,mediafilters
from deejayd.database.queries import DatabaseQueries
from deejayd.mediadb.library import AudioLibrary,VideoLibrary,NotFoundException
from deejayd.mediadb import inotify

# FIXME : Those imports should really go away one day
from deejayd.player import xine
from deejayd.ui.config import DeejaydConfig


class _TestDeejayDBLibrary(object):

    def setUp(self):
        self.dbfilename = '/tmp/testdeejayddb-'+self.testdata.getRandomString()

        # init player
        config = DeejaydConfig()
        config.set('database', 'db_type', 'sqlite')
        config.set('database', 'db_name', self.dbfilename)
        config.set('xine','audio_output',"none")
        config.set('xine','video_output',"none")

        self.db = database.init(config)
        player = xine.XinePlayer(self.db, config)
        player.init_video_support()

        self.library = self.__class__.library_class(self.db, player, \
                                                    self.testdata.getRootDir())
        self.library._update()

        self.do_update = True

    def tearDown(self):
        self.db.close()
        os.remove(self.dbfilename)

    def verifyMediaDBContent(self, testTag=True):
        time.sleep(0.2)
        if self.do_update: # First update mediadb
            self.library._update()
        else:
            time.sleep(1.5)

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
                self.assert_(False,
                    "'%s' is in directory tree but was not found in DB %s" %\
                    (root,str(allContents)))

            # First, verify directory list
            self.assertEqual(len(contents["dirs"]), len(dirs))
            for dir in dirs:
                self.assert_(dir in contents["dirs"],
                    "'%s' is in directory tree but was not found in DB %s in current root '%s'" % (dir,str(contents["dirs"]),root))

            # then, verify file list
            self.assertEqual(len(contents["files"]), len(files))
            db_files = [f["filename"] for f in contents["files"]]
            for file in files:
                (name,ext) = os.path.splitext(file)
                if ext.lower() in self.__class__.supported_ext:
                    self.assert_(file in db_files,
                    "'%s' is a file in directory tree but was not found in DB"\
                    % file)
                    relPath = os.path.join(strip_root, file)
                    if testTag:
                        self.verifyTag(relPath, inlink_path)

    def verifyTag(self, filePath, inlink_path=None):
        try: inDBfile = self.library.get_file(filePath)
        except NotFoundException:
            self.assert_(False,
                "'%s' is a file in directory tree but was not found in DB"\
                % filePath)
        else: inDBfile = inDBfile[0]

        if inlink_path:
            link_full_path = os.path.join(self.testdata.getRootDir(),
                                          inlink_path)
            abs_path = filePath[len(inlink_path)+1:]
            realFile = self.testdata.dirlinks[link_full_path].medias[abs_path]
        else:
            realFile = self.testdata.medias[filePath]
        return (inDBfile, realFile)

        for tag in ("title","artist","album","genre"):
            self.assert_(realFile[tag] == inDBfile[tag],
                "tag %s for %s different between DB and reality %s != %s" % \
                (tag,realFile["filename"],realFile[tag],inDBfile[tag]))

    def testDirlinks(self):
        self.testdata.addDirLink()
        self.verifyMediaDBContent()

        self.testdata.moveDirLink()
        self.verifyMediaDBContent()

        self.testdata.removeDirLink()
        self.verifyMediaDBContent()


class TestVideoLibrary(TestCaseWithVideoData, _TestDeejayDBLibrary):
    library_class = VideoLibrary
    supported_ext = (".mpg",".avi")

    def setUp(self):
        TestCaseWithVideoData.setUp(self)
        _TestDeejayDBLibrary.setUp(self)

    def tearDown(self):
        _TestDeejayDBLibrary.tearDown(self)
        TestCaseWithVideoData.tearDown(self)

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

    def testAddSubtitle(self):
        """Add a subtitle file in video library"""
        self.testdata.add_subtitle()
        self.verifyMediaDBContent()

    def testRemoveSubtitle(self):
        """Remove a subtitle file in video library"""
        self.testdata.remove_subtitle()
        self.verifyMediaDBContent()

    def verifyTag(self, filePath, inlink_path=None):
        (inDBfile, realFile) = _TestDeejayDBLibrary.verifyTag(self,
                                                         filePath, inlink_path)
        for tag in ('length','videowidth','videoheight','external_subtitle'):
            self.assertEqual(str(realFile[tag]), str(inDBfile[tag]))


class TestAudioLibrary(TestCaseWithAudioData, _TestDeejayDBLibrary):
    library_class = AudioLibrary
    supported_ext = (".ogg",".mp3",".mp4",".flac")

    def setUp(self):
        TestCaseWithAudioData.setUp(self)
        _TestDeejayDBLibrary.setUp(self)

    def tearDown(self):
        TestCaseWithAudioData.tearDown(self)
        _TestDeejayDBLibrary.tearDown(self)

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

    def testAddSubSubdirectory(self):
        """Add a subsubdirectory in audio library"""
        self.testdata.addSubSubdir()
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

    def testAddCover(self):
        """Add cover in audio library"""
        self.testdata.add_cover()
        self.verifyMediaDBContent()

    def testRemoveCover(self):
        """Add cover in audio library"""
        self.testdata.remove_cover()
        self.verifyMediaDBContent()

    def testSearchFile(self):
        """Search a file in audio library"""
        filter = mediafilters.Contains("genre", self.testdata.getRandomString())
        self.assertEqual([], self.library.search(filter))

        searched_genre = self.testdata.getRandomGenre()
        filter = mediafilters.Contains("genre", searched_genre)
        matched_medias_uri = []
        for path, media in self.testdata.medias.items():
            if searched_genre == media.tags['genre']:
                matched_medias_uri.append(media.tags['uri'])

        found_items_uri = [x['uri'] for x in self.library.search(filter)]

        self.assertEqual(len(matched_medias_uri), len(found_items_uri))

        found_items_uri.sort()
        matched_medias_uri.sort()
        self.assertEqual(found_items_uri, matched_medias_uri)

    def verifyTag(self,filePath, inlink_path=None):
        (inDBfile, realFile) = _TestDeejayDBLibrary.verifyTag(self, filePath,
                                                              inlink_path)
        for tag in ("title","artist","album","genre"):
            self.assert_(realFile[tag] == inDBfile[tag],
                "tag %s for %s different between DB and reality %s != %s" % \
                (tag,realFile["filename"],realFile[tag],inDBfile[tag]))


class TestInotifySupport(TestCaseWithAudioData, _TestDeejayDBLibrary):
    library_class = AudioLibrary
    supported_ext = (".ogg",".mp3",".mp4",".flac")

    def setUp(self):
        TestCaseWithAudioData.setUp(self)
        _TestDeejayDBLibrary.setUp(self)

        self.do_update = False

        # start inotify thread
        self.watcher = inotify.get_watcher(self.db, self.library, None)
        self.watcher.start()
        time.sleep(5)

    def tearDown(self):
        self.watcher.close()

        _TestDeejayDBLibrary.tearDown(self)
        TestCaseWithAudioData.tearDown(self)

    def testAddMedia(self):
        """Inotify support : Add a media in audio library"""
        self.testdata.addMedia()
        self.verifyMediaDBContent()

    def testAddSubdirectory(self):
        """Inotify support : Add a subdirectory"""
        self.testdata.addSubdir()
        self.verifyMediaDBContent()

    def testAddSubSubdirectory(self):
        """Inotify support : Add a subsubdirectory"""
        self.testdata.addSubSubdir()
        self.verifyMediaDBContent()

    def testRenameDirectory(self):
        """Inotify support : Rename a directory"""
        self.testdata.renameDir()
        self.verifyMediaDBContent(False)

    def testRemoveDirectory(self):
        """Inotify support : Remove a directory"""
        self.testdata.removeDir()
        self.verifyMediaDBContent()

    def testChangeTag(self):
        """Inotify support : Tag value change detected"""
        self.testdata.changeMediaTags()
        self.verifyMediaDBContent()

    def verifyTag(self, filePath, inlink_path=None):
        (inDBfile, realFile) = _TestDeejayDBLibrary.verifyTag(self, filePath,
                                                              inlink_path)

        for tag in ("title","artist","album","genre"):
            self.assert_(realFile[tag] == inDBfile[tag],
                "tag %s for %s different between DB and reality %s != %s" % \
                (tag,realFile["filename"],realFile[tag],inDBfile[tag]))

# vim: ts=4 sw=4 expandtab
