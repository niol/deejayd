# -*- coding: utf-8 -*-
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
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

"""
This module generates the test data.
"""
import os, sys, shutil, urllib, random, time, string

from deejayd.mediafilters import *

from testdeejayd.utils.data import sample_genres

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


class TestDataError: pass

class TestData(object):

    def __init__(self):
        # Grab some sample data
        import testdeejayd.utils.data
        self.sampleLibrary = testdeejayd.utils.data.songlibrary

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


class TestMedia(TestData):
    supportedTag = []
    ext = ""

    def __init__(self):
        self.root_path = None
        self.name = self.getRandomString(special = True) + self.ext
        self.tags = {"filename": self.name}

    def build(self, path):
        self.root_path = path
        filepath = os.path.join(path, self.name)
        shutil.copy(self.testFile, filepath)
        self.tags["uri"] = "file://%s" % urllib.quote(filepath)

        self.setRandomTag()

    def remove(self):
        os.unlink(os.path.join(self.root_path, self.name))
        self.tags = None

    def rename(self):
        newName = self.getRandomString(special = True) + self.ext
        newPath = os.path.join(self.root_path, newName)
        os.rename(os.path.join(self.root_path, self.name), newPath)
        self.tags["filename"] = newName
        self.name = newName

    def update_root_path(self, new_root):
        self.root_path = new_root

    def get_path(self):
        return os.path.join(self.root_path, self.name)
           
    def get_random_tag_value(self, tagname):
        if tagname == "date":
            value = str(self.getRandomInt(2010,1971))
        elif tagname == "tracknumber":
            value = "%02d" % self.getRandomInt(15)
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
            self.tags[tag] = unicode(value)
        tagInfo.save()
    
    def __getitem__(self, key):
        try:
            return self.tags[key]
        except KeyError:
            return None


class TestVideo(TestMedia):
    supportedTag = ("length","videowidth","videoheight",)
    ext = ".avi"
    testFile = os.path.join(DATA_DIR,"video_test.avi")

    def __init__(self):
        super(TestVideo, self).__init__()
        self.tags.update({"length": u'2', "videowidth": u'640', \
                     "videoheight": u'480', "external_subtitle": u"",\
                     "title": self.__format_title(self.name)})

    def __format_title(self, f):
        (filename, ext) = os.path.splitext(f)
        title = filename.replace(".", " ")
        title = title.replace("_", " ")
        return title.title()

    def set_subtitle(self, sub):
        if sub != "":
            self.tags["external_subtitle"] = "file://"+sub
        else:
            self.tags["external_subtitle"] = ""

    def setRandomTag(self):pass


class TestSong(TestMedia):
    supportedTag = ("tracknumber","title","genre","artist","album","date")
    
    
class TestMP3Song(TestSong):
    ext = ".mp3"
    testFile = os.path.join(DATA_DIR, "mp3_test.mp3")

    def _getTagObject(self):
        from mutagen.easyid3 import EasyID3
        return EasyID3(self.get_path())


class TestMP4Song(TestSong):
    ext = ".mp4"
    testFile = os.path.join(DATA_DIR, "mp4_test.mp4")
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

    def setRandomTag(self):
        from mutagen.mp4 import MP4
        tag_info = MP4(self.get_path())
        for tag, name in self.__translate.iteritems():
            value = unicode(self.get_random_tag_value(name))
            tag_info[tag] = value
            self.tags[name] = value

        for tag, name in self.__tupletranslate.iteritems():
            cur = self.getRandomInt(15)
            value = (cur, 15)
            tag_info[tag] = [value]
            self.tags[name] = unicode("%02d/15" % cur)

        tag_info.save()


class TestOggSong(TestSong):
    ext = ".ogg"
    testFile = os.path.join(DATA_DIR, "ogg_test.ogg")

    def _getTagObject(self):
        from mutagen.oggvorbis import OggVorbis
        return OggVorbis(self.get_path())


class TestFlacSong(TestSong):
    ext = ".flac"
    testFile = os.path.join(DATA_DIR, "flac_test.flac")

    def _getTagObject(self):
        from mutagen.flac import FLAC
        return FLAC(self.get_path())


class _TestDir(TestData):
    supported_files_class = []

    def __init__(self):
        self.is_built = False
        self.name = self.getRandomString(special = True)
        self.dirPath = None
        self.relPath = None
        self.medias = []

    def findMedia(self, filename):
        for media in self.medias:
            if media["filename"] == filename:
                return media
        raise KeyError("media %s not found" % filename)
        
    def addMedia(self, media):
        if self.is_built: 
            media.build(self.dirPath)
        self.medias.append(media)

    def addRandomMedia(self):
        media_class=self.getRandomElement(self.__class__.supported_files_class)
        self.addMedia(media_class())

    def removeMedia(self):
        m = self.getRandomElement(self.medias)
        m.remove()
        self.medias.remove(m)
                
    def build(self, destDir, rel_path = ""):
        self.relPath = os.path.join(rel_path, self.name)
        self.dirPath = os.path.join(destDir, self.name)
        if not os.path.exists(self.dirPath):
            os.mkdir(self.dirPath)
        else:
            sys.exit('folder already exists, I do not want to mess your stuff.')

        self.is_built = True
        # Add medias
        for media_class in self.__class__.supported_files_class:
            for i in range(2):
                self.addMedia(media_class())

    def rename(self):
        newName = self.getRandomString(special = True)
        root_dir = os.path.dirname(self.dirPath)
        os.rename(self.dirPath, os.path.join(root_dir, newName))
        self.name = newName
        self.dirPath = os.path.join(root_dir, newName)
        for media in self.medias:
            media.update_root_path(self.dirPath)

    def remove(self):
        shutil.rmtree(self.dirPath)
        self.build = False


class TestAudioDir(_TestDir):
    supported_files_class = (TestOggSong,TestMP3Song,TestMP4Song,TestFlacSong)

    def __init__(self):
        super(TestAudioDir, self).__init__()
        self.cover = None

    def build(self, destDir, rel_path = "", with_cover = False):
        super(TestAudioDir, self).build(destDir, rel_path)
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
    supported_files_class = (TestVideo,)

    def __init__(self):
        super(TestVideoDir, self).__init__()
        self.has_sub = False

    def build(self, destDir, rel_path = "", with_subtitle = False):
        super(TestVideoDir, self).build(destDir, rel_path)
        if with_subtitle:
            self.add_subtitle()

    def add_subtitle(self):
        sub_path = os.path.join(DATA_DIR, "sub.srt")
        for media in self.medias:
            if not media["external_subtitle"]:
                sub_name = media["filename"]
                (sub_name, ext) = os.path.splitext(sub_name)
                dest = os.path.join(self.dirPath, sub_name + ".srt")
                shutil.copy(sub_path, dest)
                media.set_subtitle(dest)
        self.has_sub = True

    def remove_subtitle(self):
        for media in self.medias:
            if media["external_subtitle"]:
                os.unlink(media["external_subtitle"].replace("file://", ""))
                media.set_subtitle("")
        self.has_sub = False


class _TestMediaCollection(TestData):

    def __init__(self):
        self.datadir = None
        self.dir_struct_written = False
        self.clean_library = True
        self.songPaths = []
        self.dirs = {}
        self.dirlinks = {}

    def cleanLibraryDirectoryTree(self):
        if self.dir_struct_written and self.clean_library:
            shutil.rmtree(self.datadir)
            for dirlink in self.dirlinks.values():
                shutil.rmtree(dirlink.datadir)

    def buildLibraryDirectoryTree(self, destDir = "/tmp"):
        # create test data directory in random subdirectory of destDir
        self.datadir = os.path.join(os.path.normpath(destDir),
                                   'testdeejayd-media' + self.getRandomString())
        if not os.path.exists(self.datadir):
            os.mkdir(self.datadir)
        else:
            sys.exit('folder already exists, I do not want to mess your stuff.')

        # Create several directories
        for i in range(self.getRandomInt(10,5)):
            self.addDir()

        # Add a subdirectories
        for i in range(self.getRandomInt(10,5)):
            self.addSubdir()

        self.dir_struct_written = True

    def get_song_paths(self):
        song_paths = []
        for dirname in self.dirs.keys():
            for m in self.dirs[dirname].medias:
                song_paths.append(os.path.join(dirname, m["filename"]))
        return song_paths

    def getRootDir(self):
        return self.datadir

    def stripRoot(self, path):
        """Strips the root directory path turning the argument into a
        path relative to the media root directory."""
        abs_path = os.path.abspath(path)
        rel_path = os.path.normpath(abs_path[len(self.getRootDir()):])

        if rel_path != '.': rel_path = rel_path.strip("/")
        else: rel_path = ''

        return rel_path

    def getMedia(self, filepath):
        dirname, filename = os.path.split(filepath)
        try:
            d = self.dirs[dirname]
        except KeyError:
            raise KeyError("folder %s not found" % dirname)
        return d.findMedia(filename)          
    
    def getRandomMedia(self):
        d = self.getRandomElement(self.dirs.values())
        return self.getRandomElement(d.medias)

    def getMedias(self):
        medias = []
        for d in self.dirs.values():
            medias.extend(d.medias)
        return medias
        
    def getDirs(self):
        return self.dirs.values()
              
    def getRandomSongPaths(self, howMuch = 1):
        """Returns the path of a random song in provided music"""
        random.seed(time.time())
        return random.sample(self.get_song_paths(), howMuch)
    
    def addMedia(self):
        dir = self.getRandomElement(self.dirs.values())
        dir.addRandomMedia()

    def renameMedia(self):
        dir = self.getRandomElement(self.dirs.values())
        media = self.getRandomElement(dir.medias)
        media.rename()

    def removeMedia(self):
        d = self.getRandomElement(self.dirs.values())
        d.removeMedia()

    def addDir(self):
        dir = self.dir_class()
        dir.build(self.datadir, "", random.choice((True, False)))

        self.dirs[dir.name] = dir

    def addSubdir(self):
        dir = self.getRandomElement(self.dirs.values())
        subdir = self.dir_class()
        subdir_path = os.path.join(self.datadir, dir.relPath)
        subdir.build(subdir_path, dir.relPath)

        self.dirs[os.path.join(dir.relPath, subdir.name)] = subdir

    def renameDir(self):
        dirname = self.getRandomElement(self.dirs.keys())
        dir = self.dirs[dirname]
        del self.dirs[dirname]

        dir.rename()
        dirpath = os.path.join(os.path.dirname(dirname), dir.name)
        self.dirs[dirpath] = dir

    def removeDir(self):
        dirKey = self.getRandomElement(self.dirs.keys())
        dir = self.dirs[dirKey]
        del self.dirs[dirKey]
        dir.remove()

    def addDirLink(self):
        where = self.getRandomElement(self.dirs.values())
        dirlink = self.__class__()
        linkname = self.getRandomString()
        linkpath = os.path.join(self.datadir, where.name, linkname)
        dirlink.buildLibraryDirectoryTree()
        self.dirlinks[linkpath] = dirlink

        os.symlink(dirlink.datadir, linkpath)

    def moveDirLink(self):
        dirlinkpath = self.getRandomElement(self.dirlinks.keys())
        linkname = os.path.basename(dirlinkpath)

        new_location = self.getRandomElement([d for d in self.dirs.keys()\
                                              if d != linkname])
        new_location = os.path.join(self.getRootDir(), new_location, linkname)
        os.rename(dirlinkpath, new_location)

        dirlink = self.dirlinks[dirlinkpath]
        del self.dirlinks[dirlinkpath]
        self.dirlinks[new_location] = dirlink

    def removeDirLink(self):
        dirlinkpath, dirlink = self.getRandomElement(self.dirlinks.items())
        os.unlink(dirlinkpath)
        dirlink.cleanLibraryDirectoryTree()
        del self.dirlinks[dirlinkpath]


class TestAudioCollection( _TestMediaCollection):
    dir_class = TestAudioDir    

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
        d = self.getRandomElement(self.dirs.values())
        media = self.getRandomElement(d.medias)
        media.setRandomTag()


class TestVideoCollection( _TestMediaCollection):
    dir_class = TestVideoDir

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
