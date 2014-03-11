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

import random, time, os
from deejayd import DeejaydError
from testdeejayd.interfaces import _TestInterfaces
from deejayd.model.mediafilters import Contains

class _PlaylistInterfaceTests(_TestInterfaces):

    def _playlistLoadMedias(self, how_many = 10, pls_name="audiopls"):
        pl = self._get_playlist(pls_name=pls_name)
        library = self._get_library(pls_name=pls_name)
        library_data = self._get_library_data(pls_name=pls_name)

        mypl = []
        media_ids = []
        for media_path in library_data.getRandomMediaPaths(how_many):
            mypl.append(library_data.getMedia(media_path)["uri"])
            self.assertAckCmd(pl.add_media_by_path(media_path))

        return mypl

    def _testPlaylistAddMediaByIds(self, pls_name="audiopls"):
        pl = self._get_playlist(pls_name=pls_name)

        # try to add a wrong id
        wrong_id = self.testdata.getRandomInt(10000, 5000)
        self.assertRaises(DeejaydError, pl.add_media_by_ids, [wrong_id])

        mypl = self._playlistLoadMedias(pls_name=pls_name)
        ddpl = pl.get()
        ddpl_uris = [media['uri'] for media in ddpl]
        for media_uri in mypl:
            self.assertTrue(media_uri in ddpl_uris)

    def _testPlaylistLoadFolders(self, pls_name="audiopls"):
        pl = self._get_playlist(pls_name=pls_name)
        library = self._get_library(pls_name=pls_name)
        library_data = self._get_library_data(pls_name=pls_name)

        # try to add a wrong id
        wrong_id = self.testdata.getRandomInt(10000, 5000)
        self.assertRaises(DeejaydError, pl.load_folders, [wrong_id])

        # test with a correct id
        lib_content = library.get_dir_content('')
        dir = library_data.getRandomElement(lib_content['directories'])
        self.assertAckCmd(pl.load_folders([dir['id']]))

        f = Contains("uri", dir["path"])
        dir_content = library.search(f)
        pl_content = pl.get()
        self.assertEqual(len(pl_content), len(dir_content))

    def _testPlaylistRemove(self, pls_name="audiopls"):
        pl = self._get_playlist(pls_name=pls_name)
        mypl = self._playlistLoadMedias(pls_name=pls_name)
        
        random.seed(time.time())
        medias_to_delete = random.sample(mypl, 3)
        self.assertAckCmd(pl.remove([media['id'] for media in pl.get()
                                     if media ['uri'] in medias_to_delete]))

        ddpl = pl.get()
        ddpl_uris = [media['uri'] for media in ddpl]
        for media_uri in mypl:
            if media_uri in medias_to_delete:
                self.assertFalse(media_uri in ddpl_uris)
            else:
                self.assertTrue(media_uri in ddpl_uris)

    def _testPlaylistClear(self, pls_name="audiopls"):
        pl = self._get_playlist(pls_name=pls_name)
        self._playlistLoadMedias(pls_name=pls_name)
        
        self.assertAckCmd(pl.clear())
        self.assertEqual(pl.get(), [])
        
    def _testPlaylistShuffle(self, pls_name="audiopls"):
        pl = self._get_playlist(pls_name=pls_name)
        mypl = self._playlistLoadMedias(pls_name=pls_name)
        
        self.assertAckCmd(pl.shuffle())
        # verify
        uris = [m["uri"] for m in pl.get()]
        self.assertNotEqual(mypl, uris)
        
    def _testPlaylistMove(self, pls_name="audiopls"):
        """Test playlist.move command"""
        pl = self._get_playlist(pls_name=pls_name)
        self._playlistLoadMedias(3, pls_name=pls_name)
        ddpl = pl.get()
        # move the first song at the end
        media_id = ddpl[0]["media_id"]
        self.assertAckCmd(pl.move([ddpl[0]["id"]], -1))
        #  verify
        ddpl = pl.get()
        self.assertEqual(media_id, ddpl[-1]["media_id"])

    def _testPlaylistSetOption(self, pls_name="audiopls"):
        pl = self._get_playlist(pls_name=pls_name)
        # unknown option
        rnd_opt = self.testdata.getRandomString()
        self.assertRaises(DeejaydError, pl.set_option, rnd_opt, 1)
        self.assertRaises(DeejaydError, pl.set_option, "playorder", rnd_opt)


        order = self.testdata.getRandomElement(("inorder", "random", "onemedia"))
        self.assertAckCmd(pl.set_option("playorder", order))
        status = pl.get_status()
        self.assertEqual(status["playorder"], order)

        #rpt = self.testdata.getRandomElement((False, True))
        #self.assertAckCmd(self.deejayd.set_option(mode, "repeat", rpt))

    def _get_playlist(self, pls_name="audiopls"):
        return getattr(self.deejayd, pls_name)

    def _get_library_data(self, pls_name="audiopls"):
        if pls_name.startswith("audio"):
            return self.test_audiodata
        return self.test_videodata

    def _get_library(self, pls_name="audiopls"):
        if pls_name.startswith("audio"):
            return self.deejayd.audiolib
        return self.deejayd.videolib


class AudioPlaylistInterfaceTests(_PlaylistInterfaceTests):

    def testAudioPlaylistAddMediaByIds(self):
        """Test audiopls.addMediaByIds command"""
        self._testPlaylistAddMediaByIds(pls_name="audiopls")

    def testAudioPlaylistLoadFolders(self):
        """Test audiopls.loadFolders command"""
        self._testPlaylistLoadFolders(pls_name="audiopls")

    def testAudioPlaylistRemove(self):
        """Test audiopls.remove command"""
        self._testPlaylistRemove(pls_name="audiopls")

    def testAudioPlaylistClear(self):
        """Test audiopls.clear command"""
        self._testPlaylistClear(pls_name="audiopls")

    def testAudioPlaylistShuffle(self):
        """Test audiopls.shuffle command"""
        self._testPlaylistShuffle(pls_name="audiopls")

    def testAudioPlaylistMove(self):
        """Test audiopls.move command"""
        self._testPlaylistMove(pls_name="audiopls")

    def testAudioPlaylistLoadPlaylist(self):
        """Test audiopls.loadPlaylist command"""
        pl = self._get_playlist(pls_name="audiopls")
        library = self._get_library(pls_name="audiopls")
        # first create a playlist
        djplname = self.testdata.getRandomString()
        pl_infos = self.deejayd.recpls.create(djplname, "static")

        how_many_songs = 3
        pl_id = pl_infos["pl_id"]
        for s_path in self.test_audiodata.getRandomMediaPaths(how_many_songs):
            self.assertAckCmd(self.deejayd.recpls.static_add_media_by_path(
                pl_id,s_path))
        pl_content = self.deejayd.recpls.get_content(pl_id)["medias"]

        # then load the playlist
        self.assertAckCmd(pl.load_playlist([pl_id]))
        ddpl = pl.get()
        # verify content
        self.assertEqual(len(ddpl), len(pl_content))
        media_ids = [s["media_id"] for s in pl_content]
        for song in ddpl:
            self.assertTrue(song["media_id"] in media_ids)


class AudioQueueInterfaceTests(_PlaylistInterfaceTests):

    def testAudioQueueAddMediaByIds(self):
        """Test audioqueue.addMediaByIds command"""
        self._testPlaylistAddMediaByIds(pls_name="audioqueue")

    def testAudioQueueRemove(self):
        """Test audioqueue.remove command"""
        self._testPlaylistRemove(pls_name="audioqueue")

    def testAudioQueueClear(self):
        """Test audioqueue.clear command"""
        self._testPlaylistClear(pls_name="audioqueue")

    def testAudioQueueMove(self):
        """Test audioqueue.move command"""
        self._testPlaylistMove(pls_name="audioqueue")

    def testAudioQueueLoadPlaylist(self):
        """Test audioqueue.loadPlaylist command"""
        pl = self._get_playlist(pls_name="audioqueue")
        library = self._get_library(pls_name="audioqueue")
        # first create a playlist
        djplname = self.testdata.getRandomString()
        pl_infos = self.deejayd.recpls.create(djplname, "static")

        how_many_songs = 3
        pl_id = pl_infos["pl_id"]
        for s_path in self.test_audiodata.getRandomMediaPaths(how_many_songs):
            self.assertAckCmd(self.deejayd.recpls.static_add_media_by_path(
                pl_id,s_path))
        pl_content = self.deejayd.recpls.get_content(pl_id)["medias"]

        # then load the playlist
        self.assertAckCmd(pl.load_playlist([pl_id]))
        ddpl = pl.get()
        # verify content
        self.assertEqual(len(ddpl), len(pl_content))
        media_ids = [s["media_id"] for s in pl_content]
        for song in ddpl:
            self.assertTrue(song["media_id"] in media_ids)


class VideoPlaylistInterfaceTests(_PlaylistInterfaceTests):

    def testVideoPlaylistAddMediaByIds(self):
        """Test videopls.addMediaByIds command"""
        self._testPlaylistAddMediaByIds(pls_name="videopls")

    def testVideoPlaylistLoadFolders(self):
        """Test videopls.loadFolders command"""
        self._testPlaylistLoadFolders(pls_name="videopls")

    def testVideoPlaylistRemove(self):
        """Test videopls.remove command"""
        self._testPlaylistRemove(pls_name="videopls")

    def testVideoPlaylistClear(self):
        """Test videopls.clear command"""
        self._testPlaylistClear(pls_name="videopls")

    def testVideoPlaylistShuffle(self):
        """Test videopls.shuffle command"""
        self._testPlaylistShuffle(pls_name="videopls")

    def testVideoPlaylistMove(self):
        """Test videopls.move command"""
        self._testPlaylistMove(pls_name="videopls")

# vim: ts=4 sw=4 expandtab