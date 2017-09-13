# Deejayd, a media player daemon
# Copyright (C) 2007-2017 Mickael Royer <mickael.royer@gmail.com>
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

import random
import time
from deejayd import DeejaydError
from testdeejayd.interfaces import _TestInterfaces
from deejayd.db.models import Contains


class _PlaylistInterfaceTests(_TestInterfaces):

    def _get_medias(self, pls_name="audiopls"):
        library = self._get_library(pls_name=pls_name)
        library_data = self._get_library_data(pls_name=pls_name)
        r_dir = library_data.get_random_dir()
        return library.get_dir_content(r_dir.rel_path)["files"]

    def _load_medias(self, pls_name="audiopls"):
        pl = self._get_playlist(pls_name=pls_name)
        files = self._get_medias(pls_name=pls_name)
        pl.load_medias([f["m_id"] for f in files])
        return files

    def _testPlaylistLoadMedias(self, pls_name="audiopls"):
        pl = self._get_playlist(pls_name=pls_name)

        # try to add a wrong id
        wrong_id = self.testdata.get_random_int(10000, 5000)
        self.assertRaises(DeejaydError, pl.load_medias, [wrong_id])

        files = self._load_medias(pls_name)
        # check the result
        ddpl = pl.get()
        ddpl_uris = [media['uri'] for media in ddpl]
        for f in files:
            self.assertTrue(f["uri"] in ddpl_uris)

    def _testPlaylistLoadFolders(self, pls_name="audiopls"):
        pl = self._get_playlist(pls_name=pls_name)
        library = self._get_library(pls_name=pls_name)
        library_data = self._get_library_data(pls_name=pls_name)

        # try to add a wrong id
        wrong_id = self.testdata.get_random_int(10000, 5000)
        pl.load_folders([wrong_id])
        self.assertEqual(len(pl.get()), 0)

        # test with a correct id
        lib_content = library.get_dir_content('')
        dir_obj = library_data.get_random_element(lib_content['directories'])
        self.assertAckCmd(pl.load_folders([dir_obj['id']]))

        f = Contains("uri", dir_obj["path"])
        dir_content = [m["m_id"] for m in library.search(f)]
        pl_content = pl.get()
        # check the content of the playlist
        self.assertEqual(len(pl_content), len(dir_content))
        for pl_entry in pl_content:
            self.assertTrue(pl_entry["m_id"] in dir_content)

    def _testPlaylistRemove(self, pls_name="audiopls"):
        pl = self._get_playlist(pls_name=pls_name)
        mypl = self._load_medias(pls_name)
        
        random.seed(time.time())
        medias_to_delete = [m["uri"] for m in random.sample(mypl, 3)]
        self.assertAckCmd(pl.remove([media['id'] for media in pl.get()
                                     if media['uri'] in medias_to_delete]))

        ddpl = pl.get()
        ddpl_uris = [media['uri'] for media in ddpl]
        for media_uri in [m["uri"] for m in mypl]:
            if media_uri in medias_to_delete:
                self.assertFalse(media_uri in ddpl_uris)
            else:
                self.assertTrue(media_uri in ddpl_uris)

    def _testPlaylistClear(self, pls_name="audiopls"):
        pl = self._get_playlist(pls_name=pls_name)
        self._load_medias(pls_name=pls_name)
        
        self.assertAckCmd(pl.clear())
        self.assertEqual(pl.get(), [])
        
    def _testPlaylistShuffle(self, pls_name="audiopls"):
        pl = self._get_playlist(pls_name=pls_name)
        mypl = [m["uri"] for m in self._load_medias(pls_name=pls_name)]
        
        self.assertAckCmd(pl.shuffle())
        # verify
        uris = [m["uri"] for m in pl.get()]
        self.assertEqual(len(mypl), len(uris))
        self.assertNotEqual(mypl, uris)
        
    def _testPlaylistMove(self, pls_name="audiopls"):
        pl = self._get_playlist(pls_name=pls_name)
        self._load_medias(pls_name=pls_name)
        ddpl = pl.get()
        # move the first song at the end
        media_id = ddpl[0]["m_id"]
        self.assertAckCmd(pl.move([ddpl[0]["id"]], -1))
        #  verify
        ddpl = pl.get()
        self.assertEqual(media_id, ddpl[-1]["m_id"])

    def _testPlaylistSetOption(self, pls_name="audiopls"):
        pl = self._get_playlist(pls_name=pls_name)
        # unknown option
        rnd_opt = self.testdata.get_random_string()
        self.assertRaises(DeejaydError, pl.set_option, rnd_opt, 1)
        self.assertRaises(DeejaydError, pl.set_option, "playorder", rnd_opt)

        order = self.testdata.get_random_element(("inorder", "random",
                                                  "onemedia"))
        self.assertAckCmd(pl.set_option("playorder", order))
        status = pl.get_status()
        self.assertEqual(status["playorder"], order)

        if pls_name != "audioqueue":
            rpt = self.testdata.get_random_element((False, True))
            self.assertAckCmd(pl.set_option("repeat", rpt))
            status = pl.get_status()
            self.assertEqual(status["playorder"], order)

    def _testLoadPlaylist(self, pls_name="audiopls"):
        pl = self._get_playlist(pls_name)
        recpls = self.deejayd.recpls
        # first create a playlist
        djplname = self.testdata.get_random_string()
        pl_infos = self.deejayd.recpls.create(djplname, "static")

        pl_id = pl_infos["pl_id"]
        media_ids = [m["m_id"] for m in self._get_medias(pls_name)]
        self.assertAckCmd(recpls.static_load_medias(pl_id, media_ids))

        # then load the playlist
        self.assertAckCmd(pl.load_playlist([pl_id]))
        ddpl = pl.get()
        # verify content
        self.assertEqual(len(ddpl), len(media_ids))
        for song in ddpl:
            self.assertTrue(song["m_id"] in media_ids)

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

    def testAudioPlaylistLoadMedias(self):
        """Test audiopls.loadMedias command"""
        self._testPlaylistLoadMedias(pls_name="audiopls")

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

    def testAudioPlaylistSetOption(self):
        """Test audiopls.setOption command"""
        self._testPlaylistSetOption(pls_name="audiopls")

    def testAudioPlaylistLoadPlaylist(self):
        """Test audiopls.loadPlaylist command"""
        self._testLoadPlaylist(pls_name="audiopls")


class AudioQueueInterfaceTests(_PlaylistInterfaceTests):

    def testAudioQueueLoadMedias(self):
        """Test audioqueue.LoadMedias command"""
        self._testPlaylistLoadMedias(pls_name="audioqueue")

    def testAudioQueueLoadFolders(self):
        """Test audioqueue.loadFolders command"""
        self._testPlaylistLoadFolders(pls_name="audioqueue")

    def testAudioQueueRemove(self):
        """Test audioqueue.remove command"""
        self._testPlaylistRemove(pls_name="audioqueue")

    def testAudioQueueClear(self):
        """Test audioqueue.clear command"""
        self._testPlaylistClear(pls_name="audioqueue")

    def testAudioQueueMove(self):
        """Test audioqueue.move command"""
        self._testPlaylistMove(pls_name="audioqueue")

    def testAudioQueueSetOption(self):
        """Test audioqueue.setOption command"""
        self._testPlaylistSetOption(pls_name="audioqueue")

    def testAudioQueueLoadPlaylist(self):
        """Test audioqueue.loadPlaylist command"""
        self._testLoadPlaylist(pls_name="audioqueue")


class VideoPlaylistInterfaceTests(_PlaylistInterfaceTests):

    def testVideoPlaylistLoadMedias(self):
        """Test videopls.LoadMedias command"""
        self._testPlaylistLoadMedias(pls_name="videopls")

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
