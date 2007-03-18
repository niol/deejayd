# -*- coding: utf-8 -*-
"""
This module generates the test data.
"""
import os, sys
import md5
import random, time, string
from xml.dom import minidom


class TestData:

    def __init__(self):
        # Grab some sample data
        import testdeejayd.data
        self.sampleLibrary = testdeejayd.data.songlibrary

    def getRandomString(self, length = 5, charset = string.letters):
        random.seed(time.time())
        return ''.join(random.sample(charset, length))


class TestSong:

    def __init__(self, tagDict):
        self.tags = tagDict

    def getFilename(self):
        return os.path.basename(self.tags['filename'])

    def getDirname(self):
        return os.path.dirname(self.tags['filename'])


class TestDir:

    def __init__(self, name):
        self.name = name
        self.songs = {}

    def addSong(self, song):
        self.songs[song.getFilename()] = song

    def create(self, destDir):
        # FIXME Not implemented
        pass

    def destroy(self):
        # FIXME Not implemented
        pass


class TestProvidedMusicCollection(TestData):

    def __init__(self, musicDir):
        self.datadir = os.path.normpath(musicDir)

        self.songPaths = []
        for root, dir, files in os.walk(self.datadir):
            for file in files:
                if file.split('.')[-1] == 'mp3':
                    self.songPaths.append(self.stripRoot(os.path.join(root,
                                                                      file)))

    def getRootDir(self):
        return self.datadir

    def stripRoot(self, path):
        """Strips the root directory path turning the argument into a
        path relative to the music root directory."""
        abs_path = os.path.abspath(path)
        rel_path = os.path.normpath(abs_path[len(self.getRootDir()):])

        if rel_path != '.':
            rel_path = '.' + rel_path

        return rel_path

    def getRandomSongPaths(self, howMuch = 1):
        """Returns the path of a random song in provided music"""
        random.seed(time.time())
        return random.sample(self.songPaths, howMuch)


class TestMusicCollection(TestProvidedMusicCollection):

    def __init__(self, data, dontClean = False):
        TestProvidedMusicCollection.__init__(self, '')

        self.dir_struct_written = False

        self.dontClean = dontClean
        self.data = data
        self.dirs = {'.': self}

        for songmeta in self.data:
            song = TestSong(songmeta)

            # Add testdir of it is not known
            if not self.dirs.has_key(song.getDirname()):
                self.dirs[song.getDirname()] = TestDir(song.getDirname())
            testdir = self.dirs[song.getDirname()]

            testdir.addSong(TestSong(songmeta))

    def cleanLibraryDirectoryTree(self):
        if self.dir_struct_written:
            # This basically is rm -r self.testdir
            for dir in self.dirs:
                dir.destroy()

    def buildLibraryDirectoryTree(self, destDir):
        # create test data directory in random subdirectory of destDir
        self.datadir = '-'.join(destDir,self.getRandomString())
        if not os.path.exists(self.datadir):
            mkdir(self.datadir)
        else:
            sys.exit(1)

        # Create each library dir
        for dir in self.dirs:
            dir.create(self.datadir)

        self.dir_struct_written = True


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
