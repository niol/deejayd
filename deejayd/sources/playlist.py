from deejayd.sources.unknown import *
from deejayd.mediadb.deejaydDB import NotFoundException 
from os import path
import random


class PlaylistNotFoundException:pass

class Playlist(UnknownSource):

    def __init__(self,library,name, content = None, id = 0):
        UnknownSource.__init__(self,library,id)

        # Init parms
        self.playlistName = name
        self.rootPath = library.getRootPath() 

        if content == None:
            # Load the content of this playlist
            self.sourceContent = self.db.getPlaylist(name)
            if len(self.sourceContent) == 0:
                if name.startswith("__") and name.endswith("__"):
                    self.sourceContent = []
                else:
                    # Playlist not found
                    raise PlaylistNotFoundException

            # Format correctly playlist content
            self.sourceContent = [self.formatMediadbPlaylistFiles(s)
                for s in self.sourceContent]

        elif isinstance(content,list):
            self.sourceContent = content


    def move(self,id,newPos,type):
        song = self.getSong(id,type)
        oldPos = song["Pos"]
        del self.sourceContent[oldPos]
        self.sourceContent.insert(newPos,song)

        # Reorder the playlist
        ids = range(0,len(self.sourceContent))
        for id in ids:
            self.sourceContent[id]["Pos"] = id

        # Increment sourceId
        self.sourceId += 1

    def shuffle(self,current):
        newPlaylist = []
        oldPlaylist = self.sourceContent
        pos = 0
        # First we have to put the current song at the first place
        if current != None:
            oldPos = current["Pos"]
            del oldPlaylist[oldPos]
            newPlaylist.append(current)
            newPlaylist[pos]["Pos"] = pos
            pos += 1

        while len(oldPlaylist) > 0:
            song = random.choice(oldPlaylist) 
            del oldPlaylist[oldPlaylist.index(song)]
            newPlaylist.append(song)
            newPlaylist[pos]["Pos"] = pos
            pos += 1

        self.sourceContent = newPlaylist
        # Increment sourceId
        self.sourceId += 1
            
    def save(self):
        # First we delete all previous record
        self.db.deletePlaylist(self.playlistName)
        # After we record the new playlist
        self.db.savePlaylist(self.sourceContent,self.playlistName)

    def erase(self):
        self.db.deletePlaylist(self.playlistName)



class PlaylistSource(UnknownSourceManagement):
    currentPlaylistName = "__djcurrent__"

    def __init__(self,player,djDB):
        UnknownSourceManagement.__init__(self,player,djDB)

        # Init parms
        self.sourceName = "playlist"
        self.db = djDB.getDB()
        self.__openPlaylists = {}
        self.playedSongs = []

        # Load current playlist
        self.currentSource = self.__openPlaylist()

    def getList(self):
        list = [pl for (pl,) in self.db.getPlaylistList() if not \
            pl.startswith("__") or not pl.endswith("__")]
        return list

    def getContent(self,playlist = None):
        playlistObj = self.__openPlaylist(playlist)
        content = playlistObj.getContent()

        if isinstance(playlist,str):
            self.__closePlaylist(playlist) 
        return content

    def addPath(self,files,playlist = None,pos = None):
        playlistObj = self.__openPlaylist(playlist)

        songs = []
        if isinstance(files,str):
            files = [files]
        for file in files:
            try: songs.extend(self.djDB.getAll(file))
            except NotFoundException:
                # perhaps it is file
                try: songs.extend(self.djDB.getFile(file))
                except NotFoundException: raise ItemNotFoundException

        playlistObj.addMediadbFiles(songs,pos)
        if playlist != None:
            self.__closePlaylist(playlist) 

    def shuffle(self, playlistName = None):
        self.currentSource.shuffle(self.currentItem)

    def move(self,id,newPos,type = "Id"):
        self.currentSource.move(id,newPos,type)

    def clear(self,playlist = None):
        playlistObj = self.__openPlaylist(playlist)

        if playlist == None:
            self.currentItem = None
            self.player.reset("playlist")
        playlistObj.clear()

        if isinstance(playlist,str):
            self.__closePlaylist(playlist) 

    def delete(self,nb,type = "Id",playlist = None):
        playlistObj = self.__openPlaylist(playlist)
        
        if playlist == None and self.currentItem != None and\
                self.currentItem[type] == nb:
            self.player.stop()
            pos = self.currentItem["Pos"]
            self.goTo(pos+1, "Pos")
        playlistObj.delete(nb,type)

        if isinstance(playlist,str):
            self.__closePlaylist(playlist) 

    def load(self,playlists,pos = None):
        songs = []
        if isinstance(playlists,str):
            playlists = [playlists]
        for playlist in playlists:
            sourceContent = Playlist(self.djDB,playlist)
            songs.extend(sourceContent.getContent())

        self.currentSource.addMediadbFiles(songs,pos)

    def save(self,playlistName):
        playlistObj = Playlist(self.djDB,playlistName,\
            self.currentSource.getContent())
        playlistObj.save()

    def rm(self,playlistName):
        Playlist(self.djDB,playlistName).erase()

    def next(self,rd,rpt):
        if self.currentItem == None:
            self.goTo(0,"Pos")
            return self.currentItem

        # Return a pseudo-random song
        l = self.currentSource.getContentLength()
        if rd and l > 0: 
            # first determine if the current song is in playedSongs
            try:
                id = self.playedSongs.index(self.currentItem["Id"])
                self.currentItem = self.currentSource.getItem(\
                    self.playedSongs[id+1],"Id")
                return self.currentItem
            except: pass

            # So we add the current song in playedSongs
            self.playedSongs.append(self.currentItem["Id"])

            # Determine the id of the next song
            values = [v for v in self.currentSource.getItemIds() \
                if v not in self.playedSongs]
            try: songId = random.choice(values)
            except: # All songs are played 
                if rpt:
                    self.playedSongs = []
                    songId = random.choice(self.currentSource.getItemIds())
                else: return None

            # Obtain the choosed song
            try: self.currentItem = self.currentSource.getItem(songId,"Id")
            except ItemNotFoundException: return None
            return self.currentItem
            
        # Reset random
        self.playedSongs = []

        currentPosition = self.currentItem["Pos"]
        if currentPosition < self.currentSource.getContentLength()-1:
            try: self.currentItem = self.currentSource.getItem(\
                self.currentItem["Pos"] + 1)
            except ItemNotFoundException: self.currentItem = None
        elif rpt:
            self.currentItem = self.currentSource.getItem(0)
        else:
            self.currentItem = None

        return self.currentItem

    def previous(self,rd,rpt):
        if self.currentItem == None:
            return None

        # Return the last pseudo-random song
        l = len(self.playedSongs)
        if rd and l > 0:
            # first determine if the current song is in playedSongs
            try:
                id = self.playedSongs.index(self.currentItem["Id"])
                if id == 0: return None
                self.currentItem = self.currentSource.getItem(\
                    self.playedSongs[id-1],"Id")
                return self.currentItem
            except ItemNotFoundException: return None 
            except ValueError: pass

            # So we add the current song in playedSongs
            self.playedSongs.append(self.currentItem["Id"])

            self.currentItem = self.currentSource.\
                getItem(self.playedSongs[l-1],"Id")
            return self.currentItem

        # Reset random
        self.playedSongs = []

        currentPosition = self.currentItem["Pos"]
        if currentPosition > 0:
            self.currentItem = self.currentSource.\
                getItem(self.currentItem["Pos"] - 1)
        else:
            self.currentItem = None

        return self.currentItem

    def goTo(self,nb,type = "Id"):
        # Reset random
        self.playedSongs = []

        return UnknownSourceManagement.goTo(self,nb,type)

    def close(self):
        states = [(str(self.currentSource.sourceId),self.sourceName+"id")]
        self.djDB.setState(states)
        self.__closePlaylist(self.__class__.currentPlaylistName)

    def getStatus(self):
        rs = [("playlist",self.currentSource.sourceId),\
            ("playlistlength",self.currentSource.getContentLength())]
        return rs

    def __openPlaylist(self,name = None):
        id = 0
        if name == None:
            name = self.__class__.currentPlaylistName
            id = self.getRecordedId()

        if name not in self.__openPlaylists:
            self.__openPlaylists[name] = Playlist(self.djDB,name,None,id)
        return self.__openPlaylists[name]
        
    def __closePlaylist(self,name):
        if name in self.__openPlaylists:
            self.__openPlaylists[name].save()
            del self.__openPlaylists[name]
        else:
            raise PlaylistNotFoundException


# vim: ts=4 sw=4 expandtab
