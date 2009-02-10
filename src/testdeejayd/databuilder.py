# -*- coding: utf-8 -*-
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
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

"""
This module generates the test data.
"""
import os, sys, shutil, urllib, random, time, string

from deejayd.mediafilters import *

from testdeejayd.data import sample_genres

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


class TestDataError: pass

class TestData(object):

    def __init__(self):
        # Grab some sample data
        import testdeejayd.data
        self.sampleLibrary = testdeejayd.data.songlibrary

    def getRandomString(self, length = 5, charset = string.letters,\
                        special = False):
        random.seed(time.time())
        rs = ''.join(random.sample(charset, length-1))
        #if special:
        #    rs += ''.join(random.sample(['é','è',"'","`","?","-","ç","à"], 2))
        return rs

    def getRandomInt(self, maxValue = 10, minValue = 1):
        random.seed(time.time())
        return random.randint(minValue, maxValue)

    def getRandomElement(self, list):
        random.seed(time.time())
        return random.sample(list, 1).pop()

    def getBadCaracter(self):
        return "\xe0"

    def getRandomGenre(self):
        return self.getRandomElement(sample_genres)

    def getSampleParmDict(self, howMuch = 2):
        parmDict = {}
        for i in range(howMuch):
            parmDict['parmName' + str(i)] = 'parmValue' + str(i)
        return parmDict

    def get_sample_filter(self):
        filter = And(Contains('artist', 'Britney'),
                     Or(Equals('genre', 'Classical'),
                        Equals('genre', 'Disco')
                     )
                    )
        return filter


class TestSong(TestData):
    supportedTag = ("tracknumber","title","genre","artist","album","date")

    def __init__(self):
        self.name = self.getRandomString(special = True) + self.ext
        self.tags = {}

    def build(self,path):
        filename = os.path.join(path, self.name)
        shutil.copy(self.testFile, filename)
        self.tags["filename"] = filename
        self.tags["uri"] = "file://%s" % urllib.quote(filename)

        self.setRandomTag()

    def remove(self):
        os.unlink(self.tags["filename"])
        self.tags = None

    def rename(self):
        newName = self.getRandomString(special = True) + self.ext
        newPath = os.path.join(os.path.dirname(self.tags['filename']),\
            newName)
        os.rename(self.tags['filename'],newPath)
        self.tags["filename"] = newPath
        self.name = newName

    def get_random_tag_value(self, tagname):
        if tagname == "date":
            value = str(self.getRandomInt(2010,1971))
        elif tagname == "tracknumber":
            value = str(self.getRandomInt(15))
        elif tagname == "genre":
            value = self.getRandomGenre()
        else:
            value = self.getRandomString(special=False)
        return value

    def setRandomTag(self):
        tagInfo = self._getTagObject()
        for tag in self.__class__.supportedTag:
            value = self.get_random_tag_value(tag)
            tagInfo[tag] = unicode(value)
            self.tags[tag] = value
        tagInfo.save()


class TestVideo(TestSong):

    def __init__(self):
        self.testFile,self.ext = os.path.join(DATA_DIR,"video_test.avi"),".avi"
        super(TestVideo, self).__init__()
        # FIXME Shoudn't videowidth and videoheight be of type int?
        self.tags = {"length": 2, "videowidth": '640', "videoheight": '480',\
                     "external_subtitle": ""}

    def __getitem__(self,key):
        try: return self.tags[key]
        except KeyError:
            return None

    def set_subtitle(self, sub):
        if sub != "":
            self.tags["external_subtitle"] = "file://"+sub
        else:
            self.tags["external_subtitle"] = ""

    def setRandomTag(self):pass


class TestMP3Song(TestSong):

    def __init__(self):
        self.testFile,self.ext = os.path.join(DATA_DIR, "mp3_test.mp3"), ".mp3"
        #self.name = self.getRandomString() + self.getBadCaracter() + self.ext
        self.name = self.getRandomString() + self.ext
        self.tags = {}

    def __getitem__(self,key):
        return key in self.tags and self.tags[key] or None

    def _getTagObject(self):
        from mutagen.easyid3 import EasyID3
        return EasyID3(self.tags["filename"])


class TestMP4Song(TestSong):
    __translate = {
        "\xa9nam": "title",
        "\xa9alb": "album",
        "\xa9ART": "artist",
        "\xa9day": "date",
        "\xa9gen": "genre",
        }
    __tupletranslate = {
        "trkn": "tracknumber",
        }

    def __init__(self):
        self.testFile,self.ext = os.path.join(DATA_DIR, "mp4_test.mp4"), ".mp4"
        super(TestMP4Song, self).__init__()

    def __getitem__(self,key):
        return key in self.tags and self.tags[key] or None

    def setRandomTag(self):
        from mutagen.mp4 import MP4
        tag_info = MP4(self.tags["filename"])
        for tag, name in self.__translate.iteritems():
            value = self.get_random_tag_value(name)
            tag_info[tag] = unicode(value)
            self.tags[name] = value

        for tag, name in self.__tupletranslate.iteritems():
            cur = self.getRandomInt(15)
            value = (cur, 15)
            tag_info[tag] = [value]
            self.tags[name] = "%d/15" % cur

        tag_info.save()

class TestOggSong(TestSong):

    def __init__(self):
        self.testFile,self.ext = os.path.join(DATA_DIR, "ogg_test.ogg"), ".ogg"
        super(TestOggSong, self).__init__()

    def __getitem__(self,key):
        return key in self.tags and self.tags[key] or None

    def _getTagObject(self):
        from mutagen.oggvorbis import OggVorbis
        return OggVorbis(self.tags["filename"])


class TestFlacSong(TestSong):

    def __init__(self):
        self.testFile,self.ext = os.path.join(DATA_DIR,"flac_test.flac"),".flac"
        super(TestFlacSong, self).__init__()

    def __getitem__(self,key):
        return key in self.tags and self.tags[key] or None

    def _getTagObject(self):
        from mutagen.flac import FLAC
        return FLAC(self.tags["filename"])


class _TestDir(TestData):

    def __init__(self):
        self.build = False
        self.name = self.getRandomString(special = True)
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
        newName = self.getRandomString(special = True)
        os.rename(os.path.join(self.root,self.name),\
                  os.path.join(self.root,newName))
        self.name = newName

    def remove(self):
        shutil.rmtree(self.dirPath)
        self.build = False


class TestAudioDir(_TestDir):

    def __init__(self):
        super(TestAudioDir, self).__init__()
        self.cover = None

    def buildContent(self, destDir, with_cover = False):
        super(TestAudioDir, self).buildContent(destDir)
        if with_cover: self.add_cover()

    def add_cover(self):
        if not self.cover:
            cover_path = os.path.join(DATA_DIR, "cover.jpg")
            self.cover = os.path.join(self.dirPath, "cover.jpg")
            shutil.copy(cover_path, self.cover)

    def remove_cover(self):
        if self.cover:
            os.unlink(self.cover)
            self.cover = None


class TestVideoDir(_TestDir):

    def __init__(self):
        super(TestVideoDir, self).__init__()
        self.has_sub = False

    def buildContent(self, destDir, with_subtitle = False):
        super(TestVideoDir, self).buildContent(destDir)
        if with_subtitle:
            self.add_subtitle()

    def add_subtitle(self):
        sub_path = os.path.join(DATA_DIR, "sub.srt")
        for item in self.items:
            if not item["external_subtitle"]:
                sub_name = os.path.basename(item["filename"])
                (sub_name, ext) = os.path.splitext(sub_name)
                dest = os.path.join(self.dirPath, sub_name + ".srt")
                shutil.copy(sub_path, dest)
                item.set_subtitle(dest)
        self.has_sub = True

    def remove_subtitle(self):
        for item in self.items:
            if item["external_subtitle"]:
                os.unlink(item["external_subtitle"].replace("file://", ""))
                item.set_subtitle("")
        self.has_sub = False


class TestProvidedMusicCollection(TestData):

    def __init__(self, musicDir):
        self.datadir = os.path.normpath(musicDir)

        self.songPaths = []
        for root, dir, files in os.walk(self.datadir):
            for file in files:
                (name,ext) = os.path.splitext(file)
                if ext.lower() in ('.mp3','.ogg','.mp4','.flac'):
                    self.songPaths.append(self.stripRoot(os.path.join(root,
                                                                        file)))

    def getRootDir(self):
        return self.datadir

    def get_song_paths(self):
        return self.songPaths

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
        return random.sample(self.get_song_paths(), howMuch)


class _TestMediaCollection(TestProvidedMusicCollection):

    def __init__(self):
        self.dir_struct_written = False
        self.clean_library = True
        self.dirs = {}
        self.medias = {}
        self.supported_files_class = ()

    def cleanLibraryDirectoryTree(self):
        if self.dir_struct_written and self.clean_library:
            shutil.rmtree(self.datadir)

    def buildLibraryDirectoryTree(self, destDir = "/tmp"):
        # create test data directory in random subdirectory of destDir
        self.datadir = os.path.join(os.path.normpath(destDir),
                                   'testdeejayd-media' + self.getRandomString())
        if not os.path.exists(self.datadir):
            os.mkdir(self.datadir)
        else:
            sys.exit(\
     'Test data temporary directory exists, I do not want to mess your stuff.')

        # Add songs in the root directory
        for media_class in self.__class__.supported_files_class:
            media = media_class()
            media.build(self.datadir)
            self.medias[media.name] = media

        # Create several directories
        for i in range(self.getRandomInt(10,5)):
            self.addDir()

        # Add a subdirectory
        self.addSubdir()

        self.dir_struct_written = True

    def get_song_paths(self):
        return self.medias.keys()

    def addMedia(self):
        dir = self.getRandomElement(self.dirs.values())

        media_class=self.getRandomElement(self.__class__.supported_files_class)
        media = media_class()
        dir.addItem(media)
        self.medias[os.path.join(dir.name, media.name)] = media

    def renameMedia(self):
        mediaKey = self.getRandomElement(self.medias.keys())
        media = self.medias[mediaKey]
        del self.medias[mediaKey]

        media.rename()
        new_path = os.path.join(os.path.dirname(mediaKey), media.name)
        self.medias[new_path] = media

    def removeMedia(self):
        mediaKeys = self.getRandomElement(self.medias.keys())
        self.medias[mediaKeys].remove()
        del self.medias[mediaKeys]

    def addDir(self):
        dir = self.dir_class()
        for media_class in self.__class__.supported_files_class:
            media = media_class()
            self.medias[os.path.join(dir.name, media.name)] = media
            dir.addItem(media)
        dir.buildContent(self.datadir, random.choice((True, False)))

        self.dirs[dir.name] = dir

    def addSubdir(self):
        dir = self.getRandomElement(self.dirs.values())
        subdir = self.dir_class()
        for media_class in self.__class__.supported_files_class:
            media = media_class()
            media_path = os.path.join(dir.name, subdir.name, media.name)
            self.medias[media_path] = media
            subdir.addItem(media)

        subdir_path = os.path.join(self.datadir, dir.name)
        subdir.buildContent(subdir_path)
        self.dirs[subdir_path] = dir

    def addSubSubdir(self):
        dir = self.getRandomElement(self.dirs.values())
        subdir, subsubdir = self.dir_class(), self.dir_class()
        for media_class in self.__class__.supported_files_class:
            media = media_class()
            media_path = os.path.join(dir.name, subdir.name, subsubdir.name,\
                    media.name)
            self.medias[media_path] = media
            subsubdir.addItem(media)

        subdir_path = os.path.join(self.datadir, dir.name)
        subdir.buildContent(subdir_path)
        self.dirs[subdir_path] = dir

        subsubdir_path = os.path.join(self.datadir, dir.name, subdir.name)
        subsubdir.buildContent(subsubdir_path)
        self.dirs[subsubdir_path] = subdir

    def renameDir(self):
        dir = self.getRandomElement(self.dirs.values())
        del self.dirs[dir.name]

        dir.rename()
        self.dirs[dir.name] = dir

    def removeDir(self):
        dir = self.getRandomElement(self.dirs.values())
        dir.remove()
        del self.dirs[dir.name]


class TestAudioCollection( _TestMediaCollection):
    dir_class = TestAudioDir
    supported_files_class = (TestOggSong,TestMP3Song,TestMP4Song,TestFlacSong)

    def remove_cover(self):
        for dir in self.dirs.values():
            if dir.cover:
                dir.remove_cover()
                return

    def add_cover(self):
        for dir in self.dirs.values():
            if not dir.cover:
                dir.add_cover()
                return

    def changeMediaTags(self):
        media = self.getRandomElement(self.medias.values())
        media.setRandomTag()


class TestVideoCollection( _TestMediaCollection):
    dir_class = TestVideoDir
    supported_files_class = (TestVideo,)

    def remove_subtitle(self):
        for dir in self.dirs.values():
            if dir.has_sub:
                dir.remove_subtitle()
                return

    def add_subtitle(self):
        for dir in self.dirs.values():
            if not dir.has_sub:
                dir.add_subtitle()
                return

# vim: ts=4 sw=4 expandtab
