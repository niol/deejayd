
from deejayd.player.player import *
from deejayd.ui.config import DeejaydConfig
from deejayd.mediadb.deejaydDB import djDB,database,NotFoundException
from os import path


class PlaylistNotFoundException:pass
class PlaylistUnknownException:pass

class Playlist:

    def __init__(self,db,name = "__djcurrent__", content = None):
        self.playlistName = name
        self.db = db 

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
        self.playlistContent = [{"dir":s[0],"filename":s[1],"position":s[3],"title":s[6],"artist":s[7],"album":s[8], \
            "genre":s[9],"tracknumber":s[10],"date":s[11],"length":s[12],"bitrate":s[13]} for s in self.playlistContent]

    def get(self):
        return self.playlistContent

    def getSong(self,position):
        song = None
        for s in self.playlistContent:
            if s["position"] == position:
                song = s
                break

        if song == None:
            raise PlaylistNotFoundException
        return song

    def addSongs(self,songs):
        playlistLength = len(self.playlistContent)
        i = 0
        for s in songs:
            pos = playlistLength+i
            self.playlistContent.append({"dir":s[0],"filename":s[1],"position":pos,})
            i += 1

    def save(self):
        # First we delete all previous record
        query = "DELETE FROM {playlist} WHERE name = ?"
        self.db.execute(query,(self.playlistName,))

        # After we record the new playlist
        query = "INSERT INTO {playlist}(name,position,dir,filename)VALUES(?,?,?,?)"
        values = [(self.playlistName,s["position"],s["dir"],s["filename"]) for s in self.playlistContent]
        self.db.executemany(query,values)

        # We commit changes
        self.db.connection.commit()

    def clear(self):
        self.playlistContent = []

    def shuffle(self):
        pass

    def delete(self):
        query = "DELETE FROM {playlist} WHERE name = ?"
        self.db.execute(query,(playlistName,))


class PlaylistManagement:
    supportedDatabase = ('sqlite')
    root_path =  DeejaydConfig().get("mediadb","music_directory")

    def __init__(self):
        # Init player
        self.player = Player()
        def on_eos():
            self.next()
        self.player.on_eos = lambda *x: on_eos()

        # Init parms
        self.currentSong = None
        self.random = False
        self.repeat = False

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
        self.currentPlaylist = Playlist(self.db)

    def getList(self):
        pass

    def getContent(self,playlist = None):
        playlistContent = isinstance(playlist,str) and Playlist(self.db,playlist) or self.currentPlaylist
        return playlistContent.get()

    def loadPlaylist(self,playlist):
        playlistContent = Playlist(self.db,playlist)
        self.currentPlaylist.addSongs(playlistContent.get())

    def addPath(self,path,playlist = None):
        playlistContent = isinstance(playlist,str) and Playlist(self.db,playlist) or self.currentPlaylist

        try:
            songs = djDB.getAll(path)
        except NotFoundException:
            # perhaps it is file
            songs = djDB.getFile(path)

        playlistContent.addSongs(songs)
        if playlist != None:
            playlistContent.save()

    def save(self,playlistName):
        playlistObj = Playlist(self.db,playlistName,self.currentPlaylist.get())
        playlistObj.save()

    def clear(self):
        self.currentSong = None
        self.player.stop()
        self.currentPlaylist.clear()
        return True

    def play(self):
        if self.player.state == PLAYER_PLAY:
            return

        if self.currentSong == None:
            try:
                self.currentSong = self.currentPlaylist.getSong(0)
            except PlaylistNotFoundException:
                return

        songPath = path.join(self.currentSong["dir"],self.currentSong["filename"])
        self.player.setSong("file://"+path.join(self.__class__.root_path,songPath))
        self.player.play()

    def pause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()

    def next(self):
        if self.currentSong == None:
            pass

        # First, we stop the player
        self.player.stop()
        currentPosition = self.currentSong["position"]
        if currentPosition < len(self.currentPlaylist.get()):
            self.currentSong = self.currentPlaylist.getSong(self.currentSong["position"] + 1)
            self.play()

    def previous(self):
        if self.currentSong == None:
            pass

        # First, we stop the player
        self.player.stop()
        currentPosition = self.currentSong["position"]
        if currentPosition > 0:
            self.currentSong = self.currentPlaylist.getSong(self.currentSong["position"] - 1)
        self.play()

    def close(self):
        # Before leave deejayd, we have to record the current playlist in the database
        self.currentPlaylist.save()
        # close the databas connection
        self.db.close


# TODO : find a better way to initialise playlist management
global djPlaylist
djPlaylist = PlaylistManagement()

# vim: ts=4 sw=4 expandtab
