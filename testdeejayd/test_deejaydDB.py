"""
Deejayd DB testing module
"""
from testdeejayd import TestCaseWithMediaData, TestCaseWithProvidedMusic
from deejayd.mediadb.database import sqliteDatabase
from deejayd.mediadb.deejaydDB import DeejaydDB, NotFoundException
import os,time

# FIXME : Those imports should really go away one day
from deejayd.player import gstreamer
from deejayd.ui.config import DeejaydConfig

class testDeejayDBWithProvidedMusic(TestCaseWithProvidedMusic):

    def setUp(self):
        TestCaseWithProvidedMusic.setUp(self)
        self.setUpDB()

    def tearDown(self):
        TestCaseWithProvidedMusic.tearDown(self)
        self.removeDB()

    def setUpDB(self):
        self.dbfilename = '/tmp/testdeejayddb-' + \
            self.testdata.getRandomString()
        self.db = sqliteDatabase(self.dbfilename)
        self.db.connect()

        self.ddb = DeejaydDB(self.db, self.testdata.getRootDir())

        # FIXME : Player shouldn't need to be initialised there. It should be
        # by the DeejayDB.
        self.ddb.setPlayer(gstreamer.Gstreamer(self.ddb, DeejaydConfig()))

        self.ddb.startUpdate()

    def removeDB(self):
        self.db.close()
        os.remove(self.dbfilename)

    def testGetDir(self):
        """Dir detected by deejayddb"""
        self.assertRaises(NotFoundException,
                        self.ddb.getDir, self.testdata.getRandomString())

        for root, dirs, files in os.walk(self.testdata.getRootDir()):
            current_root = self.testdata.stripRoot(root)
            inDBdirsDump = self.ddb.getDir(current_root)

            inDBdirs = []
            for record in inDBdirsDump:
                inDBdirs.append(record[1])

            for dir in dirs:
                self.assert_(os.path.join(current_root, dir) in inDBdirs,
                    "'%s' is in directory tree but was not found in DB" % dir)


class testDeejayDB(TestCaseWithMediaData,testDeejayDBWithProvidedMusic):

    def setUp(self):
        TestCaseWithMediaData.setUp(self)
        self.setUpDB()

    def tearDown(self):
        TestCaseWithMediaData.tearDown(self)
        self.removeDB()

    def testGetDir(self):
        """Dir detected by deejayddb"""
        self.__verifyMediaDBContent()

    def testAddDirectory(self):
        """Add a directory in deejaydb"""
        self.testdata.addDir()
        self.__verifyMediaDBContent()

    def testAddSubdirectory(self):
        """Add a subdirectory in deejaydb"""
        self.testdata.addSubdir()
        self.__verifyMediaDBContent()

    def testRenameDirectory(self):
        """Rename a directory in deejaydb"""
        self.testdata.renameDir()
        self.__verifyMediaDBContent(False)

    def testRemoveDirectory(self):
        """Remove a directory in deejaydb"""
        self.testdata.removeDir()
        self.__verifyMediaDBContent()

    def testAddMedia(self):
        """Add a media file in deejaydb"""
        self.testdata.addMedia()
        self.__verifyMediaDBContent()

    def testRenameMedia(self):
        """Rename a media file in deejaydb"""
        self.testdata.renameMedia()
        self.__verifyMediaDBContent()

    def testRemoveMedia(self):
        """Remove a media file in deejaydb"""
        self.testdata.removeMedia()
        self.__verifyMediaDBContent()

    def testChangeTag(self):
        """Tag value change detected by deejaydb"""
        self.testdata.changeMediaTags()
        self.__verifyMediaDBContent()

    def __verifyMediaDBContent(self, testTag = True):
        # First update mediadb
        time.sleep(0.5)
        self.ddb.startUpdate()
        time.sleep(0.5)

        self.assertRaises(NotFoundException,
                        self.ddb.getDir, self.testdata.getRandomString())
        self.assertRaises(NotFoundException,
                        self.ddb.getFile, self.testdata.getRandomString())

        for root, dirs, files in os.walk(self.testdata.getRootDir()):
            current_root = self.testdata.stripRoot(root)

            # First, verify directory list
            try: inDBdirs = [os.path.join(dir,fn) for (dir,fn,t,ti,ar,al,gn,\
                tn,dt,lg,bt) in self.ddb.getDir(current_root) \
                if t == "directory"] 
            except NotFoundException:
                allDirs = [os.path.join(dir,fn) for (dir,fn,t,ti,ar,al,gn,\
                                tn,dt,lg,bt) in self.ddb.getDir('') \
                                if t == "directory"]
                self.assert_(False,
                    "'%s' is in directory tree but was not found in DB %s" %\
                    (current_root,str(allDirs)))
            for dir in dirs:
                self.assert_(os.path.join(current_root, dir) in inDBdirs,
                    "'%s' is in directory tree but was not found in DB %s in currrent root %s" % (dir,str(inDBdirs),current_root))

            # then, verify file list
            inDBfiles = [os.path.join(dir,fn) for (dir,fn,t,ti,ar,al,gn,tn,dt,\
                lg,bt) in self.ddb.getDir(current_root) if t == "file"] 
            for file in files:
                (name,ext) = os.path.splitext(file)
                relPath = os.path.join(current_root, file)
                if ext.lower() in ('.mp3','.ogg'):
                    self.assert_(relPath in inDBfiles,
                    "'%s' is a file in directory tree but was not found in DB"\
                    % relPath)
                    if testTag: self.__verifyAudioTag(relPath)

    def __verifyAudioTag(self,filePath):
        try: inDBfile = self.ddb.getFile(filePath)
        except NotFoundException:
            self.assert_(False,
                "'%s' is a file in directory tree but was not found in DB"\
                % media.name)
        else: inDBfile = inDBfile[0]
        
        realFile = self.testdata.medias[filePath]
        tags = {"title": 3, "artist": 4, "album": 5}
        for tag in tags.keys():
            self.assert_(realFile[tag] == inDBfile[tags[tag]],
                "tag %s different between DB and reality %s != %s" % \
                (tag,realFile[tag],inDBfile[tags[tag]]))

# vim: ts=4 sw=4 expandtab
