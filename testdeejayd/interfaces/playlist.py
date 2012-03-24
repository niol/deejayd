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

class PlaylistInterfaceTests(_TestInterfaces):
    
    def __playlistLoadSongs(self, how_many = 10):
        pl = self.deejayd.playlist
        
        mypl = []
        for song_path in self.test_audiodata.getRandomSongPaths(how_many):
            mypl.append(self.test_audiodata.getMedia(song_path)["uri"])
            self.assertAckCmd(pl.add_path([song_path]))
        return mypl
    
    def testPlaylistAddPath(self):
        """Test playlist.addPath command"""
        pl = self.deejayd.playlist
        
        # try to add a wrong path
        wrong_path = self.testdata.getRandomString()
        self.assertRaises(DeejaydError, pl.add_path, [wrong_path])

        mypl = self.__playlistLoadSongs()
        ddpl = pl.get()
        ddpl_uris = [song['uri'] for song in ddpl["medias"]]
        for song_uri in mypl:
            self.assertTrue(song_uri in ddpl_uris)          
        
        # test with position argument
        song_path = self.test_audiodata.getRandomSongPaths(1)[0]
        song_uri = self.test_audiodata.getMedia(song_path).tags["uri"]
        pos = self.testdata.getRandomInt(9, 1)
        
        self.assertAckCmd(pl.add_path([song_path], pos))
        ddpl = pl.get()
        self.assertEqual(ddpl["medias"][pos]["uri"], song_uri)

    def testPlaylistAddSong(self):
        """Test playlist.addSong command"""
        pl = self.deejayd.playlist
        library = self.deejayd.audiolib
        
        # try to add a wrong id
        wrong_id = self.testdata.getRandomInt(10000, 5000)
        self.assertRaises(DeejaydError, pl.add_song, [wrong_id])
        
        # try with correct song id
        song_path = self.test_audiodata.getRandomSongPaths(1)[0]
        medias = library.get_dir_content(os.path.dirname(song_path))["files"]
        self.assertAckCmd(pl.add_song([m["media_id"] for m in medias]))
        for song in pl.get()["medias"]:
            self.assertTrue(song["media_id"] in [m["media_id"] for m in medias])
        
        # test with position argument
        media_id = medias[-1]["media_id"]
        pos = 0
        self.assertAckCmd(pl.add_song([media_id], pos))
        self.assertEqual(pl.get()["medias"][pos]["media_id"], media_id)
    
    def testPlaylistRemove(self):
        """Test playlist.remove command"""
        pl = self.deejayd.playlist
        mypl = self.__playlistLoadSongs()
        
        random.seed(time.time())
        songs_to_delete = random.sample(mypl, 3)
        self.assertAckCmd(pl.remove([song['id'] for song in pl.get()["medias"]\
                                      if song['uri'] in songs_to_delete]))

        ddpl = pl.get()
        ddpl_uris = [song['uri'] for song in ddpl["medias"]]
        for song_uri in mypl:
            if song_uri in songs_to_delete:
                self.assertFalse(song_uri in ddpl_uris)
            else:
                self.assertTrue(song_uri in ddpl_uris)

    def testPlaylistLoadPlaylist(self):
        """Test playlist.loadPlaylist command"""
        pl = self.deejayd.playlist
        # first create a playlist
        djplname = self.testdata.getRandomString()
        pl_infos = self.deejayd.recpls.create(djplname, "static")
        
        how_many_songs = 3
        pl_id = pl_infos["pl_id"]
        song_paths = self.test_audiodata.getRandomSongPaths(how_many_songs)
        self.assertAckCmd(self.deejayd.recpls.static_add_media(pl_id, song_paths))
        pl_content = self.deejayd.recpls.get_content(pl_id)["medias"]
        
        # then load the playlist
        self.assertAckCmd(pl.load_playlist([pl_id]))
        ddpl = pl.get()["medias"]
        # verify content
        self.assertEqual(len(ddpl), len(pl_content))
        media_ids = [s["media_id"] for s in pl_content]
        for song in ddpl:
            self.assertTrue(song["media_id"] in media_ids)

    def testPlaylistClear(self):
        """Test playlist.clear command"""
        pl = self.deejayd.playlist
        self.__playlistLoadSongs()
        
        self.assertAckCmd(pl.clear())
        self.assertEqual(pl.get()["medias"], [])
        
    def testPlaylistShuffle(self):
        """Test playlist.shuffle command"""
        pl = self.deejayd.playlist
        mypl = self.__playlistLoadSongs(10)
        
        self.assertAckCmd(pl.shuffle())
        # verify
        uris = [m["uri"] for m in pl.get()["medias"]]
        self.assertNotEqual(mypl, uris)
        
    def testPlaylistMove(self):
        """Test playlist.move command"""
        pl = self.deejayd.playlist
        self.__playlistLoadSongs(3)
        ddpl = pl.get()["medias"]
        # move the first song at the end
        media_id = ddpl[0]["media_id"]
        self.assertAckCmd(pl.move([ddpl[0]["id"]], -1))
        #  verify
        ddpl = pl.get()["medias"]
        self.assertEqual(media_id, ddpl[-1]["media_id"])
        
# vim: ts=4 sw=4 expandtab