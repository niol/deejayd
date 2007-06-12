"""
Deejayd DB testing module
"""
from testdeejayd import TestCaseWithMediaData
from deejayd.database.sqlite import SqliteDatabase
from deejayd.mediadb.library import AudioLibrary, VideoLibrary, \
                                                            NotFoundException
import os,time

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

        player = xine.XinePlayer(self.db, DeejaydConfig())
        player.init_video_support()
        self.library = self.__class__.library_class(self.db, player, \
                                                    self.testdata.getRootDir())
        self.library._update()

    def removeDB(self):
        self.db.close()
        os.remove(self.dbfilename)

    def verifyMediaDBContent(self, testTag = True):
        # First update mediadb
        time.sleep(0.5)
        self.library._update()

        self.assertRaises(NotFoundException,
                  self.library.get_dir_content, self.testdata.getRandomString())
        self.assertRaises(NotFoundException,
                  self.library.get_file, self.testdata.getRandomString())

        for root, dirs, files in os.walk(self.testdata.getRootDir()):
            current_root = self.testdata.stripRoot(root)

            # First, verify directory list
            try: inDBdirs = [os.path.join(item[0],item[1]) for item\
                    in self.library.get_dir_content(current_root) \
                    if item[2] == "directory"] 
            except NotFoundException:
                allDirs = [os.path.join(item[0],item[1]) for item\
                                in self.library.get_dir_content('') \
                                if item[2] == "directory"]
                self.assert_(False,
                    "'%s' is in directory tree but was not found in DB %s" %\
                    (current_root,str(allDirs)))
            for dir in dirs:
                self.assert_(os.path.join(current_root, dir) in inDBdirs,
                    "'%s' is in directory tree but was not found in DB %s in currrent root '%s'" % (dir,str(inDBdirs),current_root))

            # then, verify file list
            inDBfiles = [os.path.join(item[0],item[1]) for item \
                        in self.library.get_dir_content(current_root) \
                        if item[2] == "file"] 
            for file in files:
                (name,ext) = os.path.splitext(file)
                relPath = os.path.join(current_root, file)
                if ext.lower() in self.__class__.supported_ext:
                    self.assert_(relPath in inDBfiles,
                    "'%s' is a file in directory tree but was not found in DB"\
                    % relPath)
                    if testTag: self.verifyTag(relPath)


class TestVideoLibrary(TestDeejayDBLibrary):
    library_class = VideoLibrary
    supported_ext = (".mpg",".avi")

    def setUp(self):
        TestDeejayDBLibrary.setUp(self)
        self.testdata.build_video_library_directory_tree()
        self.setUpDB()

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

    def verifyTag(self,relPath):pass


class TestAudioLibrary(TestDeejayDBLibrary):
    library_class = AudioLibrary
    supported_ext = (".ogg",".mp3")

    def setUp(self):
        TestDeejayDBLibrary.setUp(self)
        self.testdata.build_audio_library_directory_tree()
        self.setUpDB()

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
        time.sleep(0.5)
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
        try: inDBfile = self.library.get_file(filePath)
        except NotFoundException:
            self.assert_(False,
                "'%s' is a file in directory tree but was not found in DB"\
                % media.name)
        else: inDBfile = inDBfile[0]
        
        realFile = self.testdata.medias[filePath]
        tags = {"title": 3, "artist": 4, "album": 5}
        for tag in tags.keys():
            self.assert_(realFile[tag] == inDBfile[tags[tag]],
                "tag %s for %s different between DB and reality %s != %s" % \
                (tag,realFile["filename"],realFile[tag],inDBfile[tags[tag]]))


# vim: ts=4 sw=4 expandtab