
from deejayd.ui.config import DeejaydConfig
from deejayd.mediadb.deejaydDB import djDB,database,NotFoundException
from os import path
import random


class PlaylistNotFoundException:pass
class SongNotFoundException:pass
class PlaylistUnknownException:pass

class Playlist:
    root_path =  DeejaydConfig().get("mediadb","music_directory")

    def __init__(self,db,name, content = None):
        # Init parms
        self.playlistName = name
        self.db = db 
        self.__songId = 0 
        self.playlistId = 0

        if content == None:
            # Load the content of this playlist
            self.playlistContent = self.db.getPlaylist(name)
            if len(self.playlistContent) == 0:
                if name ==  "__djcurrent__":
                    self.playlistContent = []
                else:
                    raise PlaylistNotFoundException

            # Format correctly playlist content
            self.playlistContent = [{"dir":s[0],"filename":s[1],"Pos":s[3],"Id":self.__getSongId(),"Title":s[6],\
                "Artist":s[7],"Album":s[8],"Genre":s[9],"Track":s[10],"Date":s[11],"Time":s[12],"bitrate":s[13],\
                "uri":"file://"+path.join(self.__class__.root_path,path.join(s[0],s[1]))} for s in self.playlistContent]

        elif isinstance(content,list):
            self.playlistContent = content


    def get(self):
        return self.playlistContent

    def getLength(self):
        return len(self.playlistContent)

    def getSong(self,position, type = "Pos"):
        song = None
        for s in self.playlistContent:
            if s[type] == position:
                song = s
                break

        if song == None:
            raise SongNotFoundException
        return song

    def getIds(self):
        return [s["Id"] for s in self.playlistContent]

    def addSongsFromLibrary(self,songs):
        playlistLength = len(self.playlistContent)
        i = 0
        for s in songs:
            pos = playlistLength+i
            self.playlistContent.append({"dir":s[0],"filename":s[1],"Pos":pos,"Id":self.__getSongId(),"Title":s[3],
                "Artist":s[4],"Album":s[5],"Genre":s[6],"Track":s[7],"Date":s[8],"Time":s[9],"bitrate":s[10],\
                "uri":"file://"+path.join(self.__class__.root_path,path.join(s[0],s[1]))})
            i += 1
        # Increment playlistId
        self.playlistId += len(songs)

    def addSongsFromPlaylist(self,songs):
        playlistLength = len(self.playlistContent)
        i = 0
        for s in songs:
            pos = playlistLength+i
            self.playlistContent.append({"dir":s["dir"],"filename":s["filename"],"Pos":pos,"Id":self.__getSongId(),\
                "Title":s["Title"],"Artist":s["Artist"],"Album":s["Album"],"Genre":s["Genre"],"Track":s["Track"],\
                "Date":s["Date"],"Time":s["Time"],"bitrate":s["bitrate"],\
                "uri":s["uri"]})
            i += 1
        # Increment playlistId
        self.playlistId += len(songs)

    def clear(self):
        self.playlistContent = []
        # Increment playlistId
        self.playlistId += 1

    def delete(self,nb,type):
        i = 0
        for s in self.playlistContent:
            if s[type] == nb:
                break
            i += 1
        if i == len(self.playlistContent):
            raise SongNotFoundException
        pos = self.playlistContent[i]["Pos"]
        del self.playlistContent[i]

        # Now we must reorder the playlist
        for s in self.playlistContent:
            if s["Pos"] > pos:
                s["Pos"] -= 1

        # Increment playlistId
        self.playlistId += 1

    def shuffle(self,current):
        pass

    def save(self):
        # First we delete all previous record
        self.db.deletePlaylist(self.playlistName)
        # After we record the new playlist
        self.db.savePlaylist(self.playlistContent,self.playlistName)

    def erase(self):
        self.db.deletePlaylist(self.playlistName)

    def __getSongId(self):
        self.__songId += 1
        return self.__songId


class PlaylistManagement:
    currentPlaylistName = "__djcurrent__"

    def __init__(self,player):
        # Init player
        self.player = player
        # Open a connection to the database
        self.db = database.openConnection()
        self.db.connect()
        # Init parms
        self.__openPlaylists = {}
        self.currentSong = None
        self.playedSongs = []

        # Load current playlist
        self.currentPlaylist = self.__openPlaylist()

    def getList(self):
        return self.db.getPlaylistList()

    def getContent(self,playlist = None):
        playlistObj = self.__openPlaylist(playlist)
        content = playlistObj.get()

        if isinstance(playlist,str):
            self.__closePlaylist(playlist) 
        return content

    def addPath(self,path,playlist = None):
        playlistObj = self.__openPlaylist(playlist)

        try:
            songs = djDB.getAll(path)
        except NotFoundException:
            # perhaps it is file
            songs = djDB.getFile(path)

        playlistObj.addSongsFromLibrary(songs)
        if isinstance(playlist,str):
            self.__closePlaylist(playlist) 

    def shuffle(self):
        self.currentPlaylist.shuffle(self.currentSong)

    def clear(self,playlist = None):
        playlistObj = self.__openPlaylist(playlist)

        if playlist == None:
            self.currentSong = None
            self.player.reset()
        playlistObj.clear()

        if isinstance(playlist,str):
            self.__closePlaylist(playlist) 

    def delete(self,nb,type = "Id",playlist = None):
        playlistObj = self.__openPlaylist(playlist)
        
        if playlist == None and self.currentSong != None and self.currentSong[type] == nb:
            self.player.next()
        playlistObj.delete(nb,type)

        if isinstance(playlist,str):
            self.__closePlaylist(playlist) 

    def load(self,playlist):
        playlistContent = Playlist(self.db,playlist)
        self.currentPlaylist.addSongsFromPlaylist(playlistContent.get())

    def save(self,playlistName):
        playlistObj = Playlist(self.db,playlistName,self.currentPlaylist.get())
        playlistObj.save()

    def rm(self,playlistName):
        Playlist(self.db,playlistName).erase()

    def next(self,rd,rpt):
        if self.currentSong == None:
            return None

        # Return a pseudo-random song
        l = self.currentPlaylist.getLength()
        if rd and l > 0: 
            # first determine if the current song is in playedSongs
            try:
                id = self.playedSongs.index(self.currentSong["Id"])
                self.currentSong = self.currentPlaylist.getSong(self.playedSongs[id+1],"Id")
                return self.currentSong
            except: pass

            # So we add the current song in playedSongs
            self.playedSongs.append(self.currentSong["Id"])

            # Determine the id of the next song
            values = [v for v in self.currentPlaylist.getIds() if v not in self.playedSongs]
            try: songId = random.choice(values)
            except: # All songs are played 
                if rpt:
                    self.playedSongs = []
                    songId = random.choice(self.currentPlaylist.getIds())
                else: return None

            # Obtain the choosed song
            try: self.currentSong = self.currentPlaylist.getSong(songId,"Id")
            except SongNotFoundException: return None
            return self.currentSong
            
        # Reset random
        self.playedSongs = []

        currentPosition = self.currentSong["Pos"]
        if currentPosition < len(self.currentPlaylist.get())-1:
            try: self.currentSong = self.currentPlaylist.getSong(self.currentSong["Pos"] + 1)
            except SongNotFoundException: return None
        elif rpt:
            self.currentSong = self.currentPlaylist.getSong(0)
        else:
            return None

        return self.currentSong

    def previous(self,rd,rpt):
        if self.currentSong == None:
            return None

        # Return the last pseudo-random song
        l = len(self.playedSongs)
        if rd and l > 0:
            # first determine if the current song is in playedSongs
            try:
                id = self.playedSongs.index(self.currentSong["Id"])
                if id == 0: return None
                self.currentSong = self.currentPlaylist.getSong(self.playedSongs[id-1],"Id")
                return self.currentSong
            except SongNotFoundException: return None 
            except ValueError: pass

            # So we add the current song in playedSongs
            self.playedSongs.append(self.currentSong["Id"])

            self.currentSong = self.currentPlaylist.getSong(self.playedSongs[l-1],"Id")
            return self.currentSong

        # Reset random
        self.playedSongs = []

        currentPosition = self.currentSong["Pos"]
        if currentPosition > 0:
            self.currentSong = self.currentPlaylist.getSong(self.currentSong["Pos"] - 1)
        else:
            return None

        return self.currentSong

    def getCurrent(self):
        if self.currentSong == None:
            try: self.currentSong = self.currentPlaylist.getSong(0)
            except SongNotFoundException: pass

        return self.currentSong

    def goTo(self,nb,type = "Id"):
        try: self.currentSong = self.currentPlaylist.getSong(nb,type)
        except SongNotFoundException: self.currentSong = None

        # Reset random
        self.playedSongs = []

        return self.currentSong
        
    def close(self):
        self.__closePlaylist(self.__class__.currentPlaylistName)
        self.db.close()

    def getStatus(self):
        rs = [("playlistlength",self.currentPlaylist.getLength()),("playlist",self.currentPlaylist.playlistId)]
        return rs

    def __openPlaylist(self,name = None):
        if name == None:
            name = self.__class__.currentPlaylistName

        if name not in self.__openPlaylists:
            self.__openPlaylists[name] = Playlist(self.db,name)
        return self.__openPlaylists[name]
        
    def __closePlaylist(self,name):
        if name in self.__openPlaylists:
            self.__openPlaylists[name].save()
            del self.__openPlaylists[name]
        else:
            raise PlaylistNotFoundException


# vim: ts=4 sw=4 expandtab
