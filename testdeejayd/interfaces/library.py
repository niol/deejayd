# Deejayd, a media player daemon
# Copyright (C) 2007-2012 Mickael Royer <mickael.royer@gmail.com>
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

import os

from deejayd import DeejaydError
from testdeejayd.interfaces import require_video_support, _TestInterfaces
from deejayd.model.mediafilters import *

class LibraryInterfaceTests(_TestInterfaces):

    #
    # Test update command
    #
    def __testLibraryUpdate(self, library_type):
        library = getattr(self.deejayd, library_type + "lib")
        last_update = self.deejayd.get_stats()[library_type + "_library_update"]

        update_infos = library.update(sync=True)
        for key in (library_type + '_updating_db',):
            self.assertTrue(key in update_infos)
        new_update = self.deejayd.get_stats()[library_type + "_library_update"]

        self.assertTrue(int(last_update) <= int(new_update))

    def testLibraryAudioUpdate(self):
        """Test update command for audio library"""
        self.__testLibraryUpdate("audio")

    @require_video_support
    def testLibraryVideoUpdate(self):
        """Test update command for video library"""
        self.__testLibraryUpdate("video")

    #
    # Test getDirContent command
    #
    def __testLibraryGetDirContent(self, library_type):
        library = getattr(self.deejayd, library_type + "lib")
        testdata = getattr(self, "test_" + library_type + "data")

        # first, test with an unknown folder
        rand_folder = testdata.getRandomString()
        self.assertRaises(DeejaydError, library.get_dir_content, rand_folder)

        # now, test with an known folder
        directories = testdata.dirs.keys()
        dir = testdata.getRandomElement(directories)
        medias = library.get_dir_content(dir)["files"]

        self.assertEqual(len(medias), len(testdata.dirs[dir].medias))
        for m in medias:
            path = os.path.join(dir, m["filename"])
            try: equ_item = testdata.getMedia(path)
            except KeyError:
                self.assertTrue(False, "media %s not found in the lib : %s" \
                                % (path, str(testdata.medias.keys())))
            for tag in equ_item.supportedTag:
                self.assertEqual(unicode(equ_item.tags[tag]), unicode(m[tag]),
                                 "tag %s doesn't match for media %s" \
                                 % (tag, m["filename"]))

    def testLibraryAudioGetDirContent(self):
        """Test getDirContent command for audio library"""
        self.__testLibraryGetDirContent("audio")

    @require_video_support
    def testLibraryVideoGetDirContent(self):
        """Test getDirContent command for video library"""
        self.__testLibraryGetDirContent("video")

    #
    # Test search command
    #
    def __testLibrarySearch(self, library_type):
        library = getattr(self.deejayd, library_type + "lib")
        testdata = getattr(self, "test_" + library_type + "data")

        # search an unknown terms
        f = Equals("title", testdata.getRandomString())
        self.assertEqual(library.search(f), [])

        # search with an unknown type
        #f = Equals(testdata.getRandomString(), testdata.getRandomString())
        #self.assertRaises(DeejaydError, library.search, f)

        # search a known terms
        media = testdata.getRandomMedia()
        f = Equals("title", media["title"])
        ans = library.search(f)
        self.assertTrue(len(ans) > 0)

    def testLibraryAudioSearch(self):
        """Test search command for audio library"""
        self.__testLibrarySearch("audio")

    @require_video_support
    def testLibraryVideoSearch(self):
        """Test search command for video library"""
        self.__testLibrarySearch("video")

    #
    # Test setRating command
    #
    def __testLibrarySetRating(self, library_type):
        library = getattr(self.deejayd, library_type + "lib")
        testdata = getattr(self, "test_" + library_type + "data")

        ans = library.get_dir_content()
        dir = testdata.getRandomElement(ans["directories"])
        ans = library.get_dir_content(dir["name"])
        files = ans["files"]
        file_ids = [f["media_id"] for f in files]
        f = In("id", file_ids)
        # wrong rating
        self.assertRaises(DeejaydError, library.set_rating, f, "9")

        self.assertAckCmd(library.set_rating(f, "4"))
        ans = library.get_dir_content(dir["name"])
        for f in ans["files"]:
            self.assertEqual(4, int(f["rating"]))

    @require_video_support
    def testLibraryVideoSetRating(self):
        """Test setRating command for video library"""
        self.__testLibrarySetRating("video")

    def testLibraryAudioSetRating(self):
        """Test setRating command for audio library"""
        self.__testLibrarySetRating("audio")
    #
    # Test tagList command
    #
    def testLibraryAudioTagList(self):
        tag = 'artist'
        filter = Or(Equals('genre', self.test_audiodata.getRandomGenre()),
                    Equals('genre', self.test_audiodata.getRandomGenre()))

        expected_tag_list = []

        for song_info in self.test_audiodata.getMedias():
            matches = False
            for f in filter.filterlist:
                if song_info.tags['genre'] == f.pattern:
                    matches = True
            if matches:
                if song_info.tags[tag] not in expected_tag_list:
                    expected_tag_list.append(song_info.tags[tag])

        result = self.deejayd.audiolib.tag_list(tag, filter)

        for tagvalue in expected_tag_list:
            self.assertTrue(tagvalue in result)

# vim: ts=4 sw=4 expandtab
