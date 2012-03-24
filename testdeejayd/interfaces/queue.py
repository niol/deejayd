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

class QueueInterfaceTests(_TestInterfaces):

    def __queueLoadSongs(self, how_many = 10):
        q = self.deejayd.queue
        
        myq = []
        for song_path in self.test_audiodata.getRandomSongPaths(how_many):
            myq.append(self.test_audiodata.getMedia(song_path).tags["uri"])
            self.assertAckCmd(q.add_path([song_path]))
        return myq
    
    def testQueueAddPath(self):
        """Test queue.addPath command"""
        q = self.deejayd.queue
        
        # try to add a wrong path
        wrong_path = self.testdata.getRandomString()
        self.assertRaises(DeejaydError, q.add_path, [wrong_path])

        myq = self.__queueLoadSongs()
        ddq = q.get()
        ddq_uris = [song['uri'] for song in ddq["medias"]]
        for song_uri in myq:
            self.assertTrue(song_uri in ddq_uris)          
        
        # test with position argument
        song_path = self.test_audiodata.getRandomSongPaths(1)[0]
        song_uri = self.test_audiodata.getMedia(song_path).tags["uri"]
        pos = self.testdata.getRandomInt(9, 1)
        
        self.assertAckCmd(q.add_path([song_path], pos))
        ddq = q.get()
        self.assertEqual(ddq["medias"][pos]["uri"], song_uri)
    
    def testQueueAddSong(self):
        """Test queue.addSong command"""
        q = self.deejayd.queue
        library = self.deejayd.audiolib
        
        # try to add a wrong id
        wrong_id = self.testdata.getRandomInt(10000, 5000)
        self.assertRaises(DeejaydError, q.add_song, [wrong_id])
        
        # try with correct song id
        song_path = self.test_audiodata.getRandomSongPaths(1)[0]
        medias = library.get_dir_content(os.path.dirname(song_path))["files"]
        self.assertAckCmd(q.add_song([m["media_id"] for m in medias]))
        for song in q.get()["medias"]:
            self.assertTrue(song["media_id"] in [m["media_id"] for m in medias])
        
        # test with position argument
        media_id = medias[-1]["media_id"]
        pos = 0
        self.assertAckCmd(q.add_song([media_id], pos))
        self.assertEqual(q.get()["medias"][pos]["media_id"], media_id)
    
    def testQueueRemove(self):
        """Test queue.remove command"""
        q = self.deejayd.queue
        myq = self.__queueLoadSongs()
        
        random.seed(time.time())
        songs_to_delete = random.sample(myq, 3)
        self.assertAckCmd(q.remove([song['id'] for song in q.get()["medias"]\
                                      if song['uri'] in songs_to_delete]))

        ddq = q.get()
        ddq_uris = [song['uri'] for song in ddq["medias"]]
        for song_uri in myq:
            if song_uri in songs_to_delete:
                self.assertFalse(song_uri in ddq_uris)
            else:
                self.assertTrue(song_uri in ddq_uris)
    
    def testQueueLoadPlaylist(self):
        """Test queue.loadPlaylist command"""
        q = self.deejayd.queue
        # first create a playlist
        djplname = self.testdata.getRandomString()
        pl_infos = self.deejayd.recpls.create(djplname, "static")
        
        how_many_songs = 3
        pl_id = pl_infos["pl_id"]
        song_paths = self.test_audiodata.getRandomSongPaths(how_many_songs)
        self.assertAckCmd(self.deejayd.recpls.static_add_media(pl_id, song_paths))
        pl_content = self.deejayd.recpls.get_content(pl_id)["medias"]
        
        # then load the playlist in the queue
        self.assertAckCmd(q.load_playlist([pl_id]))
        ddq = q.get()["medias"]
        # verify content of the queue
        self.assertEqual(len(ddq), len(pl_content))
        media_ids = [s["media_id"] for s in pl_content]
        for song in ddq:
            self.assertTrue(song["media_id"] in media_ids)
        
    def testQueueClear(self):
        """Test queue.clear command"""
        q = self.deejayd.queue
        self.__queueLoadSongs()
        
        self.assertAckCmd(q.clear())
        self.assertEqual(q.get()["medias"], [])
        
    def testQueueMove(self):
        """Test queue.move command"""
        q = self.deejayd.queue
        self.__queueLoadSongs(3)
        ddq = q.get()["medias"]
        # move the first song at the end
        media_id = ddq[0]["media_id"]
        self.assertAckCmd(q.move([ddq[0]["id"]], -1))
        #  verify
        ddq = q.get()["medias"]
        self.assertEqual(media_id, ddq[-1]["media_id"])
        
# vim: ts=4 sw=4 expandtab