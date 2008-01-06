# Deejayd, a media player daemon
# Copyright (C) 2007 Mickael Royer <mickael.royer@gmail.com>
#                    Alexandre Rossi <alexandre.rossi@gmail.com>
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

from deejayd.sources._base import ItemNotFoundException,UnknownSource,\
                            UnknownSourceManagement
from deejayd.mediadb.library import NotFoundException
from os import path
import random


class PlaylistNotFoundException:pass

class Playlist(UnknownSource):

    def __init__(self,db,library,name, content = None, id = 0):
        UnknownSource.__init__(self,db,library,id)

        # Init parms
        self.playlist_name = name

        if content == None:
            # Load the content of this playlist
            self.source_content = self.db.get_playlist(name)
            if len(self.source_content) == 0:
                if name.startswith("__") and name.endswith("__"):
                    self.source_content = []
                else: raise PlaylistNotFoundException # Playlist not found

            # Format correctly playlist content
            self.source_content = [self.format_playlist_files(s)
                for s in self.source_content]

        elif isinstance(content,list):
            self.source_content = content


    def move(self,ids,new_pos,type):
        songs = []
        for id in ids:
            songs.append(self.get_item(id,type))
        old_source_content = self.source_content
        self.source_content = []
        for index,item in enumerate(old_source_content):
            if index == new_pos:
                self.source_content.extend(songs)
            if item not in songs:
                self.source_content.append(item)

        # Reorder the playlist
        ids = range(0,len(self.source_content))
        for id in ids:
            self.source_content[id]["pos"] = id
        # Increment sourceId
        self.source_id += 1

    def shuffle(self,current):
        new_playlist = []
        old_playlist = self.source_content
        pos = 0
        # First we have to put the current song at the first place
        if current != None:
            old_pos = current["pos"]
            del old_playlist[old_pos]
            new_playlist.append(current)
            new_playlist[pos]["pos"] = pos
            pos += 1

        while len(old_playlist) > 0:
            song = random.choice(old_playlist)
            del old_playlist[old_playlist.index(song)]
            new_playlist.append(song)
            new_playlist[pos]["pos"] = pos
            pos += 1

        self.source_content = new_playlist
        # Increment sourceId
        self.source_id += 1

    def save(self):
        # First we delete all previous record
        self.erase()
        # After we record the new playlist
        self.db.save_playlist(self.source_content,self.playlist_name)

    def erase(self):
        self.db.delete_playlist(self.playlist_name)



class PlaylistSource(UnknownSourceManagement):
    current_playlist_name = "__djcurrent__"
    name = "playlist"

    def __init__(self,db,library):
        UnknownSourceManagement.__init__(self,db,library)

        # Init parms
        self.__open_playlists = {}

        # Load current playlist
        self.current_source = self.__open_playlist()

    def get_list(self):
        list = [pl for (pl,) in self.db.get_playlist_list() if not \
            pl.startswith("__") or not pl.endswith("__")]
        return list

    def get_content(self,playlist = None):
        playlist_obj = self.__open_playlist(playlist)
        content = playlist_obj.get_content()

        if isinstance(playlist,str):
            self.__close_playlist(playlist)
        return content

    def add_path(self,paths,playlist = None,pos = None):
        playlist_obj = self.__open_playlist(playlist)

        songs = []
        if isinstance(paths,str):
            paths = [paths]
        for path in paths:
            try: songs.extend(self.library.get_all_files(path))
            except NotFoundException:
                # perhaps it is file
                try: songs.extend(self.library.get_file(path))
                except NotFoundException: raise ItemNotFoundException

        playlist_obj.add_files(songs,pos)
        if playlist != None:
            self.__close_playlist(playlist)

    def shuffle(self, playlist_name = None):
        playlist_obj = self.__open_playlist(playlist_name)
        playlist_obj.shuffle(self.current_item)

        if isinstance(playlist_name,str):
            self.__close_playlist(playlist_name)

    def move(self,id,new_pos,type = "id"):
        self.current_source.move(id,new_pos,type)

    def clear(self,playlist = None):
        playlist_obj = self.__open_playlist(playlist)

        if playlist == None:
            self.current_item = None
        playlist_obj.clear()

        if isinstance(playlist,str):
            self.__close_playlist(playlist)

    def delete(self,nb,type = "id",playlist = None):
        playlist_obj = self.__open_playlist(playlist)

        if playlist == None and self.current_item != None and\
                self.current_item[type] == nb:
            pos = self.current_item["pos"]
        playlist_obj.delete(nb,type)

        if isinstance(playlist,str):
            self.__close_playlist(playlist)

    def load_playlist(self,playlists,pos = None):
        songs = []
        if isinstance(playlists,str):
            playlists = [playlists]
        for playlist in playlists:
            source_content = Playlist(self.db,self.library,playlist)
            songs.extend(source_content.get_content())

        self.current_source.add_files(songs,pos)

    def save(self,playlist_name):
        playlist_obj = Playlist(self.db,self.library,playlist_name,\
            self.current_source.get_content())
        playlist_obj.save()

    def rm(self,playlist_name):
        Playlist(self.db,self.library,playlist_name).erase()

    def close(self):
        states = [(str(self.current_source.source_id),self.__class__.name+"id")]
        self.db.set_state(states)
        self.__close_playlist(self.__class__.current_playlist_name)

    def __open_playlist(self,name = None):
        id = 0
        if name == None:
            name = self.__class__.current_playlist_name
            id = self.get_recorded_id() + 1

        if name not in self.__open_playlists:
            self.__open_playlists[name] = Playlist(self.db,self.library,name,\
                                                        None,id)
        return self.__open_playlists[name]

    def __close_playlist(self,name):
        if name in self.__open_playlists:
            self.__open_playlists[name].save()
            del self.__open_playlists[name]
        else:
            raise PlaylistNotFoundException


# vim: ts=4 sw=4 expandtab
