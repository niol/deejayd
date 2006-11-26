# -*- coding: utf-8 -*-
"""
This module generates the test data.
"""
import os, sys
import md5
import random, time, string
from xml.dom import minidom


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


class TestMusicCollection(TestDir):

    def __init__(self, data, dontClean = False):
        TestDir.__init__(self, '.')

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

    def getRandomString(self, length = 5, charset = string.letters):
        random.seed(time.time())
        return ''.join(random.sample(charset, length))


class TestCommand:

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

    def getRandomString(self, length = 5, charset = string.letters):
        random.seed(time.time())
        return ''.join(random.sample(charset, length))

    def createSimpleOkanswer(self,cmdName):
        rsp = self.xmldoc.createElement("response")
        rsp.setAttribute("name",cmdName)
        rsp.setAttribute("type","ack")

        self.xmlroot.appendChild(rsp)
        return self.xmldoc.toxml('utf-8')

    def isError(self,rsp,cmdName = ""):
        xmldoc = minidom.parseString(rsp)
        errs = xmldoc.getElementsByTagName("error")

        if len(errs) > 0: return True
        else: return False

# vim: ts=4 sw=4 expandtab
