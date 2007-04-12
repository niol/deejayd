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
        self.rootPath = library.getAudioRootPath() 

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
            id = self.getRecordedId() + 1

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
