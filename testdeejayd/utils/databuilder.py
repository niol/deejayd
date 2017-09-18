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
import os
import copy
import sys
import shutil
import urllib
import random
import time
import string
from mutagen.easyid3 import EasyID3
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC
from deejayd.db.models import And, Equals, Contains, Or
from testdeejayd.utils.data import sample_genres


random.seed(time.time())
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


class TestDataError(Exception): 
    pass


class TestData(object):

    def __init__(self):
        # Grab some sample data
        import testdeejayd.utils.data
        self.sample_library = testdeejayd.utils.data.songlibrary

    def get_random_string(self, length=5, charset=string.letters):
        rs = ''.join(random.sample(charset, length - 1))
        return rs

    def get_random_int(self, max_value=10, min_value=1):
        return random.randint(min_value, max_value)

    def get_random_element(self, elt_list):
        return random.sample(elt_list, 1).pop()

    def get_bad_caracter(self):
        return "\xe0"

    def get_random_genre(self):
        return self.get_random_element(sample_genres)

    def get_sample_parm_dict(self, howMuch=2):
        parm_dict = {}
        for i in range(howMuch):
            parm_dict['parmName' + str(i)] = 'parmValue' + str(i)
        return parm_dict

    def get_sample_filter(self):
        filter = And(Contains(tag='artist', pattern='Britney'),
                     Or(Equals(tag='genre', pattern='Classical'),
                        Equals(tag='genre', pattern='Disco')))
        return filter


class TestMedia(TestData):
    SUPPORTED_TAGS = []
    EXT = ""
    FILE = None

    def __init__(self):
        self.root_path = None
        self.filepath = None
        self.name = self.get_random_string() + self.EXT
        self.tags = {"filename": self.name}

    def build(self, path):
        self.root_path = path
        self.filepath = os.path.join(path, self.name)
        shutil.copy(self.FILE, self.filepath)
        self.tags["uri"] = "file://%s" % urllib.quote(self.filepath)

        self.set_random_tags()

    def remove(self):
        os.unlink(self.filepath)
        self.tags = None

    def rename(self):
        new_name = self.get_random_string() + self.EXT
        new_path = os.path.join(self.root_path, new_name)
        os.rename(self.filepath, new_path)
        self.tags["filename"] = new_name
        self.name = new_name
        self.filepath = new_path

    def update_root_path(self, new_root):
        self.root_path = new_root
        self.filepath = os.path.join(new_root, self.name)

    def get_path(self):
        return self.filepath

    def get_random_tag_value(self, tag_name):
        if tag_name == "date":
            value = str(self.get_random_int(2010, 1971))
        elif tag_name == "tracknumber":
            value = "%02d" % self.get_random_int(15)
        elif tag_name == "genre":
            value = self.get_random_genre()
        else:
            value = self.get_random_string()
        return value

    def set_random_tags(self):
        tag_info = self._get_tag_object()
        for tag in self.SUPPORTED_TAGS:
            value = self.get_random_tag_value(tag)
            tag_info[tag] = unicode(value)
            self.tags[tag] = unicode(value)
        tag_info.save()

    def __getitem__(self, key):
        try:
            return self.tags[key]
        except KeyError:
            return None


class TestVideo(TestMedia):
    SUPPORTED_TAGS = ("length", "width", "height",)
    EXT = ".avi"
    FILE = os.path.join(DATA_DIR, "video_test.avi")

    def __init__(self):
        super(TestVideo, self).__init__()
        self.tags.update({
            "length": 2.0,
            "width": 640,
            "height": 480,
            "external_subtitle": u"",
            "title": self.__format_title(self.name)
        })

    def __format_title(self, f):
        (filename, ext) = os.path.splitext(f)
        title = filename.replace(".", " ")
        title = title.replace("_", " ")
        return title.title()

    def set_subtitle(self, sub):
        if sub != "":
            self.tags["external_subtitle"] = "file://" + sub
        else:
            self.tags["external_subtitle"] = ""

    def set_random_tags(self):
        pass


class TestSong(TestMedia):
    SUPPORTED_TAGS = (
        "tracknumber",
        "title",
        "genre",
        "artist",
        "album",
        "date"
    )


class TestMP3Song(TestSong):
    EXT = ".mp3"
    FILE = os.path.join(DATA_DIR, "mp3_test.mp3")

    def _get_tag_object(self):
        return EasyID3(self.get_path())


class TestMP4Song(TestSong):
    EXT = ".mp4"
    FILE = os.path.join(DATA_DIR, "mp4_test.mp4")
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

    def set_random_tags(self):
        tag_info = MP4(self.get_path())
        for tag, name in self.__translate.iteritems():
            value = unicode(self.get_random_tag_value(name))
            tag_info[tag] = value
            self.tags[name] = value

        for tag, name in self.__tupletranslate.iteritems():
            cur = self.get_random_int(15)
            value = (cur, 15)
            tag_info[tag] = [value]
            self.tags[name] = unicode("%02d/15" % cur)

        tag_info.save()


class TestOggSong(TestSong):
    EXT = ".ogg"
    FILE = os.path.join(DATA_DIR, "ogg_test.ogg")

    def _get_tag_object(self):
        return OggVorbis(self.get_path())


class TestFlacSong(TestSong):
    EXT = ".flac"
    FILE = os.path.join(DATA_DIR, "flac_test.flac")

    def _get_tag_object(self):
        print(self.get_path())
        return FLAC(self.get_path())


class _TestDir(TestData):
    SUPPORTED_FILES = []
    FILE_NUMBER = 2

    def __init__(self):
        self.is_built = False
        self.name = self.get_random_string()
        self.dir_path = None
        self.rel_path = None
        self.medias = []

    def find_media(self, filename):
        for media in self.medias:
            if media["filename"] == filename:
                return media
        raise KeyError("media %s not found" % filename)

    def add_media(self, media):
        if self.is_built:
            media.build(self.dir_path)
        self.medias.append(media)

    def add_random_media(self):
        media_class = self.get_random_element(self.SUPPORTED_FILES)
        self.add_media(media_class())

    def remove_media(self):
        m = self.get_random_element(self.medias)
        m.remove()
        self.medias.remove(m)

    def build(self, dest, rel_path=""):
        self.rel_path = os.path.join(rel_path, self.name)
        self.dir_path = os.path.join(dest, self.name)
        if not os.path.exists(self.dir_path):
            os.mkdir(self.dir_path)
        else:
            sys.exit("folder already exists, I do'nt want to mess your stuff.")

        self.is_built = True
        # Add medias
        for media_class in self.SUPPORTED_FILES:
            for i in range(self.FILE_NUMBER):
                self.add_media(media_class())

    def rename(self):
        new_name = self.get_random_string()
        root_dir = os.path.dirname(self.dir_path)
        os.rename(self.dir_path, os.path.join(root_dir, new_name))
        self.name = new_name
        self.dir_path = os.path.join(root_dir, new_name)
        for media in self.medias:
            media.update_root_path(self.dir_path)

    def update_parent_path(self, p_path):
        self.dir_path = os.path.join(p_path, self.name)
        for media in self.medias:
            media.update_root_path(self.dir_path)

    def remove(self):
        shutil.rmtree(self.dir_path)
        self.build = False


class TestAudioDir(_TestDir):
    SUPPORTED_FILES = (TestOggSong, TestMP3Song, TestMP4Song)

    def __init__(self):
        super(TestAudioDir, self).__init__()
        self.cover = None

    def build(self, dest, rel_path="", with_cover=False):
        super(TestAudioDir, self).build(dest, rel_path)
        if with_cover:
            self.add_cover()

    def add_cover(self):
        if not self.cover:
            cover_path = os.path.join(DATA_DIR, "cover.jpg")
            self.cover = os.path.join(self.dir_path, "cover.jpg")
            shutil.copy(cover_path, self.cover)

    def remove_cover(self):
        if self.cover:
            os.unlink(self.cover)
            self.cover = None


class TestVideoDir(_TestDir):
    SUPPORTED_FILES = (TestVideo,)
    FILE_NUMBER = 3

    def __init__(self):
        super(TestVideoDir, self).__init__()
        self.has_sub = False

    def build(self, dest, rel_path="", with_subtitle=False):
        super(TestVideoDir, self).build(dest, rel_path)
        if with_subtitle:
            self.add_subtitle()

    def add_subtitle(self):
        sub_path = os.path.join(DATA_DIR, "sub.srt")
        for media in self.medias:
            if not media["external_subtitle"]:
                sub_name = media["filename"]
                (sub_name, ext) = os.path.splitext(sub_name)
                dest = os.path.join(self.dir_path, sub_name + ".srt")
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
    DIR_CLS = None

    def __init__(self):
        self.datadir = None
        self.dir_struct_written = False
        self.clean_library = True
        self.song_paths = []
        self.dirs = {}
        self.dirlinks = {}

    def clean(self):
        if self.dir_struct_written and self.clean_library:
            shutil.rmtree(self.datadir)
            for dirlink in self.dirlinks.values():
                shutil.rmtree(dirlink.datadir)

    def build(self, dest="/tmp"):
        # create test data directory in random subdirectory of destDir
        self.datadir = os.path.join(os.path.normpath(dest),
                                    'testdeejayd-media' +
                                    self.get_random_string())
        if not os.path.exists(self.datadir):
            os.mkdir(self.datadir)
        else:
            sys.exit("folder already exists, I don't want to mess your stuff.")

        for i in range(self.get_random_int(10, 5)):
            self.add_dir()
        for i in range(self.get_random_int(10, 5)):
            self.add_subdir()

        self.dir_struct_written = True

    def get_media_paths(self):
        song_paths = []
        for dirname in self.dirs.keys():
            for m in self.dirs[dirname].medias:
                song_paths.append(os.path.join(dirname, m["filename"]))
        return song_paths

    def get_root_dir(self):
        return self.datadir

    def strip_root(self, path):
        """Strips the root directory path turning the argument into a
        path relative to the media root directory."""
        return self.strip_path(path, self.get_root_dir())

    def strip_path(self, path, root_dir):
        abs_path = os.path.abspath(path)
        rel_path = os.path.normpath(abs_path[len(root_dir):])

        if rel_path != '.':
            rel_path = rel_path.strip("/")
        else:
            rel_path = ''

        return rel_path

    def get_media(self, filepath):
        dirname, filename = os.path.split(filepath)
        try:
            d = self.dirs[dirname]
        except KeyError:
            raise KeyError("folder %s not found" % dirname)
        return d.find_media(filename)

    def get_random_media(self):
        d = self.get_random_element(self.dirs.values())
        return self.get_random_element(d.medias)

    def get_random_medias(self, how_much):
        d = self.get_random_element(self.dirs.values())
        return self.get_random_element(d.medias)

    def get_medias(self):
        medias = []
        for d in self.dirs.values():
            medias.extend(d.medias)
        return medias

    def get_dirs(self):
        return self.dirs.values()

    def get_random_dir(self):
        return self.get_random_element(self.dirs.values())

    def get_random_media_paths(self, how_much=1):
        """Returns the path of a random song in provided music"""
        return random.sample(self.get_media_paths(), how_much)

    def add_media(self):
        d = self.get_random_element(self.dirs.values())
        d.add_random_media()

    def rename_media(self):
        folder = self.get_random_element(self.dirs.values())
        media = self.get_random_element(folder.medias)
        media.rename()

    def remove_media(self):
        d = self.get_random_element(self.dirs.values())
        d.remove_media()

    def add_dir(self):
        d = self.DIR_CLS()
        d.build(self.datadir, "", random.choice((True, False)))

        self.dirs[d.name] = d

    def add_subdir(self):
        d = self.get_random_element(self.dirs.values())
        subdir = self.DIR_CLS()
        subdir_path = os.path.join(self.datadir, d.rel_path)
        subdir.build(subdir_path, d.rel_path)

        self.dirs[os.path.join(d.rel_path, subdir.name)] = subdir

    def rename_dir(self):
        dirname = self.get_random_element(self.dirs.keys())
        d = self.dirs[dirname]
        subdirs = {} 
        for d_path in copy.copy(self.dirs):
            if d_path.startswith(dirname+"/"):
                subdirs[self.strip_path(d_path, dirname)] = self.dirs[d_path]
                del self.dirs[d_path]

        d.rename()
        dirpath = os.path.join(os.path.dirname(dirname), d.name)
        self.dirs[dirpath] = d
        # update subdirs
        for sub_path in subdirs:
            newpath = os.path.join(dirpath, sub_path)
            subdirs[sub_path].update_parent_path(os.path.dirname(newpath))
            self.dirs[newpath] = subdirs[sub_path]

    def remove_dir(self):
        dirname = self.get_random_element(self.dirs.keys())
        d = self.dirs[dirname]
        d.remove()
        del self.dirs[dirname]

    def add_dir_link(self):
        where = self.get_random_element(self.dirs.values())
        dirlink = self.__class__()
        linkname = self.get_random_string()
        linkpath = os.path.join(self.datadir, where.name, linkname)
        dirlink.build()
        self.dirlinks[linkpath] = dirlink

        os.symlink(dirlink.datadir, linkpath)

    def move_dir_link(self):
        dirlinkpath = self.get_random_element(self.dirlinks.keys())
        linkname = os.path.basename(dirlinkpath)

        new_location = self.get_random_element([d for d in self.dirs.keys()
                                                if d != linkname])
        new_location = os.path.join(self.get_root_dir(), new_location, 
                                    linkname)
        os.rename(dirlinkpath, new_location)

        dirlink = self.dirlinks[dirlinkpath]
        del self.dirlinks[dirlinkpath]
        self.dirlinks[new_location] = dirlink

    def remove_dir_link(self):
        dirlinkpath, dirlink = self.get_random_element(self.dirlinks.items())
        os.unlink(dirlinkpath)
        dirlink.clean()
        del self.dirlinks[dirlinkpath]


class TestAudioCollection(_TestMediaCollection):
    DIR_CLS = TestAudioDir

    def remove_cover(self):
        for d in self.dirs.values():
            if d.cover:
                d.remove_cover()
                return

    def add_cover(self):
        for d in self.dirs.values():
            if not d.cover:
                d.add_cover()
                return

    def change_media_tags(self):
        d = self.get_random_element(self.dirs.values())
        media = self.get_random_element(d.medias)
        media.set_random_tags()


class TestVideoCollection(_TestMediaCollection):
    DIR_CLS = TestVideoDir

    def remove_subtitle(self):
        for d in self.dirs.values():
            if d.has_sub:
                d.remove_subtitle()
                return

    def add_subtitle(self):
        for d in self.dirs.values():
            if not d.has_sub:
                d.add_subtitle()
                return
