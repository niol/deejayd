# -*- coding: utf-8 -*-
"""
This module generates the test data.
"""
import os, sys, shutil
import md5
import random, time, string
from xml.dom import minidom

class TestDataError: pass

class TestData:

    def __init__(self):
        # Grab some sample data
        import testdeejayd.data
        self.sampleLibrary = testdeejayd.data.songlibrary

    def getRandomString(self, length = 5, charset = string.letters):
        random.seed(time.time())
        return ''.join(random.sample(charset, length))

    def getRandomInt(self, maxValue = 10, minValue = 1):
        random.seed(time.time())
        return random.randint(minValue, maxValue)

    def getRandomElement(self, list):
        random.seed(time.time())
        return random.sample(list, 1).pop()


class TestSong(TestData):
    supportedTag = ("tracknumber","title","genre","artist","album","date")

    def __init__(self):
        self.name = self.getRandomString() + self.ext
        self.tags = {}

    def build(self,path):
        shutil.copy(self.testFile,path) 
        filename = os.path.join(path, self.name)
        os.rename(os.path.join(path, os.path.basename(self.testFile)), filename)
        self.tags["filename"] = filename 

        self.setRandomTag()

    def remove(self):
        os.unlink(self.tags["filename"])
        self.tags = None

    def rename(self):
        newName = self.getRandomString() + self.ext
        newPath = os.path.join(os.path.dirname(self.tags['filename']),\
            newName)
        os.rename(self.tags['filename'],newPath)
        self.tags["filename"] = newPath
        self.name = newName

    def setRandomTag(self):
        tagInfo = self._getTagObject()
        for tag in self.__class__.supportedTag:
            if tag == "date": value = str(self.getRandomInt(2010,1971))
            elif tag == "tracknumber": value = str(self.getRandomInt(15))
            else: value = self.getRandomString()

            tagInfo[tag] = unicode(value)
            self.tags[tag] = value

        tagInfo.save()


class TestMP3Song(TestSong):

    def __init__(self):
        self.testFile,self.ext = "testdeejayd/data/mp3_test.mp3", ".mp3"
        TestSong.__init__(self)

    def __getitem__(self,key):
        return key in self.tags and self.tags[key] or None

    def _getTagObject(self):
        from mutagen.easyid3 import EasyID3
        return EasyID3(self.tags["filename"])


class TestOggSong(TestSong):

    def __init__(self):
        self.testFile,self.ext = "testdeejayd/data/ogg_test.ogg", ".ogg"
        TestSong.__init__(self)

    def __getitem__(self,key):
        return key in self.tags and self.tags[key] or None

    def _getTagObject(self):
        from mutagen.oggvorbis import OggVorbis
        return OggVorbis(self.tags["filename"])


class TestDir(TestData):

    def __init__(self):
        self.build = False
        self.name = self.getRandomString()
        self.root = None
        self.items = []

    def addItem(self, item):
        if self.build: item.build(self.dirPath)
        self.items.append(item)

    def buildContent(self, destDir):
        self.dirPath = os.path.join(destDir,self.name)
        os.mkdir(self.dirPath)
        for item in self.items:
            item.build(self.dirPath)
        self.build = True
        self.root = destDir

    def rename(self):
        newName = self.getRandomString()
        os.rename(os.path.join(self.root,self.name),\
                  os.path.join(self.root,newName))
        self.name = newName

    def remove(self):
        shutil.rmtree(self.dirPath)
        self.build = False
       
    def renameItem(self):
        item = self.getRandomElement(self.items)
        item.rename()

    def removeItem(self):
        item = self.getRandomElement(self.items)
        if self.build: item.remove()
        self.items.remove(item)
        

class TestProvidedMusicCollection(TestData):

    def __init__(self, musicDir):
        self.datadir = os.path.normpath(musicDir)

        self.songPaths = []
        for root, dir, files in os.walk(self.datadir):
            for file in files:
                (name,ext) = os.path.splitext(file)
                if ext.lower() in ('.mp3','.ogg'):
                    self.songPaths.append(self.stripRoot(os.path.join(root,
                                                                        file)))

    def getRootDir(self):
        return self.datadir

    def stripRoot(self, path):
        """Strips the root directory path turning the argument into a
        path relative to the music root directory."""
        abs_path = os.path.abspath(path)
        rel_path = os.path.normpath(abs_path[len(self.getRootDir()):])

        if rel_path != '.': rel_path = rel_path.strip("/")
        else: rel_path = ''

        return rel_path

    def getRandomSongPaths(self, howMuch = 1):
        """Returns the path of a random song in provided music"""
        random.seed(time.time())
        return random.sample(self.songPaths, howMuch)


class TestMediaCollection(TestProvidedMusicCollection):

    def __init__(self):
        self.dir_struct_written = False
        self.dirs = {} 
        self.medias = {} 

    def cleanLibraryDirectoryTree(self):
        if self.dir_struct_written:
            shutil.rmtree(self.datadir)

    def buildMusicDirectoryTree(self, destDir = "/tmp"):
        # create test data directory in random subdirectory of destDir
        self.datadir = os.path.join(destDir,
                                   'testdeejayd-music' + self.getRandomString())
        if not os.path.exists(self.datadir):
            os.mkdir(self.datadir)
        else:
            sys.exit('Test data temporary directory exists, I do not want to mess your stuff.')

        # Add songs in the root directory
        for media in (TestOggSong(),TestMP3Song()):
            media.build(self.datadir)
            self.medias[media.name] = media

        # Create several directories
        for i in range(self.getRandomInt(10,5)):
            self.addDir()

        # Add a subdirectory
        self.addSubdir()

        self.dir_struct_written = True

    def getRootDir(self):
        return self.datadir 

    def addMedia(self):
        dir = self.getRandomElement(self.dirs.values())

        media = TestOggSong()
        dir.addItem(media)
        self.medias[dir.name+"/"+media.name] = media

    def renameMedia(self):
        mediaKey = self.getRandomElement(self.medias.keys())
        media = self.medias[mediaKey]
        del self.medias[mediaKey]

        media.rename()
        self.medias[os.path.dirname(mediaKey) + "/" + media.name] = media

    def removeMedia(self):
        mediaKeys = self.getRandomElement(self.medias.keys())
        self.medias[mediaKeys].remove()
        del self.medias[mediaKeys]

    def addDir(self):
        dir = TestDir()
        for media in (TestOggSong(),TestMP3Song()):
            self.medias[dir.name+"/"+media.name] = media
            dir.addItem(media)
        dir.buildContent(self.datadir)

        self.dirs[dir.name] = dir

    def addSubdir(self):
        dir = self.getRandomElement(self.dirs.values())
        subdir = TestDir()
        for media in (TestOggSong(),TestMP3Song()):
            self.medias[dir.name+"/"+subdir.name+"/"+media.name] = media
            subdir.addItem(media)
        subdir.buildContent(self.datadir+"/"+dir.name)

        self.dirs[self.datadir+"/"+dir.name] = dir

    def renameDir(self):
        dir = self.getRandomElement(self.dirs.values())
        del self.dirs[dir.name]

        dir.rename()
        self.dirs[dir.name] = dir

    def removeDir(self):
        dir = self.getRandomElement(self.dirs.values())
        dir.remove()
        del self.dirs[dir.name]

    def changeMediaTags(self):
        media = self.getRandomElement(self.medias.values())
        media.setRandomTag()

class TestCommand(TestData):

    def __init__(self):
        self.xmldoc = minidom.Document()
        self.xmlroot = self.xmldoc.createElement("deejayd")
        self.xmldoc.appendChild(self.xmlroot)

    def createXMLCmd(self,cmdName,args = {}):
        cmd = self.xmldoc.createElement("command")
        cmd.setAttribute("name",cmdName)
        for k in args.keys():
            arg = self.xmldoc.createElement("arg")
            arg.setAttribute("name",k)
            arg.appendChild(self.xmlDoc.createTextNode(args[k]))
            cmd.appendChild(arg)

        self.xmlroot.appendChild(cmd)
        return self.xmldoc.toxml()

    def createRandomXMLCmd(self):
        rdCmd = self.getRandomString()
        return self.createXMLCmd(self,rdCmd)

    def createRandomLineCmd(self):
        return self.getRandomString()

    def createSimpleOkanswer(self,cmdName):
        rsp = self.xmldoc.createElement("response")
        rsp.setAttribute("name",cmdName)
        rsp.setAttribute("type","Ack")

        self.xmlroot.appendChild(rsp)
        return self.xmldoc.toxml('utf-8')

    def isError(self,rsp,cmdName = ""):
        xmldoc = minidom.parseString(rsp)
        errs = xmldoc.getElementsByTagName("error")

        if len(errs) > 0: return True
        else: return False

# vim: ts=4 sw=4 expandtab
