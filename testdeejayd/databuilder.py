# -*- coding: utf-8 -*-
"""
This module generates the test data.
"""
import os, sys
import md5
import random, time, string


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

    def __del__(self):
        if self.dir_struct_written:
            # This basically is rm -r self.testdir
            for root, dir, files in os.walk(self.datadir):
                if not self.dontClean:
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))

    def buildLibraryDirectoryTree(self, destDir):
        # create test data directory in random subdirectory of destDir
        self.datadir = '-'.join(destDir,self.getRandomString())
        if not os.path.exists(self.datadir):
            mkdir(self.datadir)
        else:
            sys.exit(1)
        self.dir_struct_written = True

    def getRandomString(self, length = 5, charset = string.letters):
        random.seed(time.time())
        return ''.join(random.sample(charset, length))


# vim: ts=4 sw=4 expandtab
