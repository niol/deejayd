
from deejayd.ui.config import DeejaydConfig
from deejayd.mediadb.deejaydDB import djDB,database,NotFoundException
from os import path


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

        if content == None:
            # Load the content of this playlist
            query = "SELECT p.dir, p.filename, p.name, p.position, l.dir, l.filename, l.title, l.artist, l.album, l.genre, \
                l.tracknumber, l.date, l.length, l.bitrate FROM {library} l INNER JOIN {playlist} p ON p.dir = l.dir AND \
                p.filename = l.filename WHERE p.name = ? ORDER BY p.position"
            self.db.execute(query,(name,))
            self.playlistContent = self.db.cursor.fetchall()
            if len(self.playlistContent) == 0:
                if name ==  "__djcurrent__":
                    self.playlistContent = []
                else:
                    raise PlaylistNotFoundException

        elif isinstance(content,list):
            self.playlistContent = content

        # Format correctly playlist content
        self.playlistContent = [{"dir":s[0],"filename":s[1],"Pos":s[3],"Id":self.__getSongId(),"Title":s[6],\
            "Artist":s[7],"Album":s[8],"Genre":s[9],"Track":s[10],"Date":s[11],"Time":s[12],"bitrate":s[13],\
            "uri":path.join(self.__class__.root_path,path.join(s[0],s[1]))} for s in self.playlistContent]

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

    def addSongsFromLibrary(self,songs):
        playlistLength = len(self.playlistContent)
        i = 0
        for s in songs:
            pos = playlistLength+i
            self.playlistContent.append({"dir":s[0],"filename":s[1],"Pos":pos,"Id":self.__getSongId(),"Title":s[3],
                "Artist":s[4],"Album":s[5],"Genre":s[6],"Track":s[7],"Date":s[8],"Time":s[9],"bitrate":s[10],\
                "uri":path.join(self.__class__.root_path,path.join(s[0],s[1]))})
            i += 1

    def addSongsFromPlaylist(self,songs):
        pass

    def clear(self):
        self.playlistContent = []

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

    def shuffle(self,current):
        pass

    def save(self):
        # First we delete all previous record
        query = "DELETE FROM {playlist} WHERE name = ?"
        self.db.execute(query,(self.playlistName,))

        # After we record the new playlist
        query = "INSERT INTO {playlist}(name,position,dir,filename)VALUES(?,?,?,?)"
        values = [(self.playlistName,s["Pos"],s["dir"],s["filename"]) for s in self.playlistContent]
        self.db.executemany(query,values)

        # We commit changes
        self.db.connection.commit()

    def erase(self):
        query = "DELETE FROM {playlist} WHERE name = ?"
        self.db.execute(query,(playlistName,))

    def __getSongId(self):
        self.__songId += 1
        return self.__songId


class PlaylistManagement:
    supportedDatabase = ('sqlite')
    currentPlaylistName = "__djcurrent__"

    def __init__(self,player):
        # Init player
        self.player = player

        # Init parms
        self.__openPlaylists = {}
        self.currentSong = None
        self.random = 0
        self.repeat = 0

        # Open a connection to the database
        try:
            db_type =  DeejaydConfig().get("mediadb","db_type")
        except:
            raise SystemExit("You do not choose a database.Verify your config file.")

        if db_type in self.__class__.supportedDatabase:
            self.db =  getattr(database,db_type+"Database")()
            self.db.connect()
        else:
            raise SystemExit("You choose a database which is not supported.Verify your config file.")

        # Load current playlist
        self.currentPlaylist = self.__openPlaylist()

    def getList(self):
        pass

    def getContent(self,playlist = None):
        playlistObj = self.__openPlaylist(playlist)
        content = playlistObj.get()

        if isinstance(playlist,str):
            self.__closePlaylist(playlist) 
        return content

    def loadPlaylist(self,playlist):
        playlistContent = Playlist(self.db,playlist)
        self.currentPlaylist.addSongsFromPlaylist(playlistContent.get())

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

    def save(self,playlistName):
        playlistObj = Playlist(self.db,playlistName,self.currentPlaylist.get())
        playlistObj.save()

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

    def next(self):
        if self.currentSong == None:
            return None

        currentPosition = self.currentSong["Pos"]
        if currentPosition < len(self.currentPlaylist.get()):
            self.currentSong = self.currentPlaylist.getSong(self.currentSong["Pos"] + 1)
        elif self.repeat:
            self.currentSong = self.currentPlaylist.getSong(0)
        else:
            return None

        return self.currentSong

    def previous(self):
        if self.currentSong == None:
            return None

        currentPosition = self.currentSong["Pos"]
        if currentPosition > 0:
            self.currentSong = self.currentPlaylist.getSong(self.currentSong["Pos"] - 1)
        else:
            return None

        return self.currentSong

    def getCurrentSong(self):
        if self.currentSong == None:
            try: self.currentSong = self.currentPlaylist.getSong(0)
            except SongNotFoundException: pass

        return self.currentSong

    def goTo(self,nb,type = "Id"):
        try: self.currentSong = self.currentPlaylist.getSong(nb,type)
        except SongNotFoundException: self.currentSong = None

        return self.currentSong
        
    def close(self):
        self.__closePlaylist(self.__class__.currentPlaylistName)
        self.db.close()

    def getStatus(self):
        rs = [("random",self.random),("repeat",self.repeat),("playlistlength",self.currentPlaylist.getLength())]
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
