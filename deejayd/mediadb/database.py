"""
 Class and methods to manage database
"""

from deejayd.ui.config import DeejaydConfig
from os import path
import sys

def strEncode(data):
    """Convert a basestring to a valid UTF-8 str."""
    filesystem_charset = DeejaydConfig().get("mediadb","filesystem_charset")
    if isinstance(data, str):
        return data.decode(filesystem_charset, "replace").encode("utf-8")
    elif isinstance(data, unicode):
        return data.encode("utf-8")
    
    return data


class databaseExeption: pass

class UnknownDatabase:

    def __init__(self):
        pass

    def _initialise(self):
        pass

    def connect(self):
        pass

    def execute(self,cur,query,parm = None):
        pass

    def executemany(self,cur,query,parm):
        pass

    def close(self):
        pass


class Database(UnknownDatabase):
    
    #
    # Playlist requests
    #
    def getPlaylist(self,playlistName):
        query = "SELECT p.dir, p.filename, p.name, p.position, l.dir, l.filename, l.title, l.artist, l.album, l.genre, \
            l.tracknumber, l.date, l.length, l.bitrate FROM {library} l INNER JOIN {playlist} p ON p.dir = l.dir AND \
            p.filename = l.filename WHERE p.name = ? ORDER BY p.position"
        self.execute(query,(playlistName,))
        return self.cursor.fetchall()

    def deletePlaylist(self,playlistName):
        self.execute("DELETE FROM {playlist} WHERE name = ?",(playlistName,))
        self.connection.commit()

    def savePlaylist(self,content,playlistName):
        values = [(playlistName,s["Pos"],s["dir"],s["filename"]) for s in content]
        query = "INSERT INTO {playlist}(name,position,dir,filename)VALUES(?,?,?,?)"
        self.executemany(query,values)
        self.connection.commit()

    def getPlaylistList(self):
        self.db.execute("SELECT name FROM {playlist}")

    #
    # Stat requests
    #
    def recordMediaDBStat(self):
        # Get the number of songs
        self.execute("SELECT filename FROM {library} WHERE type = 'file'")
        songs = len(self.cursor.fetchall())
        # Get the number of artist
        self.execute("SELECT DISTINCT artist FROM {library} WHERE type = 'file'")
        artists = len(self.cursor.fetchall())
        # Get the number of album
        self.execute("SELECT DISTINCT album FROM {library} WHERE type = 'file'")
        albums = len(self.cursor.fetchall())

        # record in the database  
        values = [(songs,"songs"),(artists,"artists"),(albums,"albums")]
        self.executemany("UPDATE {stat} SET value = ? WHERE name = ?",values)
        self.connection.commit()

    def getMediaDBStat(self):
        self.execute("SELECT * FROM {stat}")
        return self.cursor.fetchall()

    def setStat(self,type,value):
        self.execute("UPDATE {stat} SET value = ? WHERE name = ?" \
            ,(value,type))
        self.connection.commit()

    def getStat(self,type):
        self.execute("SELECT value FROM {stat} WHERE name = ?",(type,))
        (rs,) =  self.cursor.fetchone()

        return rs


class sqliteDatabase(Database):

    def __init__(self,db_file):
        self.db_file = db_file

    def _initialise(self):
        # creation of tables
        self.execute("CREATE TABLE {library}(dir TEXT,filename TEXT,type TEXT,title TEXT,artist TEXT,album TEXT,\
            genre TEXT, tracknumber INT, date TEXT, length INT, bitrate INT, PRIMARY KEY (dir,filename))")
        self.execute("CREATE TABLE {radio}(name TEXT,url1 TEXT, url2 TEXT, url3 TEXT,PRIMARY KEY (name))")
        self.execute("CREATE TABLE {playlist}(name TEXT,position INT, dir TEXT, filename TEXT,PRIMARY KEY (name,position))")
        self.execute("CREATE TABLE {stat}(name TEXT,value INT,PRIMARY KEY (name))")

        values = [("db_update",0),("songs",0),("artists",0),("albums",0)]
        self.executemany("INSERT INTO {stat}(name,value)VALUES(?,?)",values)
        self.connection.commit()

    def connect(self):
        from pysqlite2 import dbapi2 as sqlite
        init = path.isfile(self.db_file) and (0,) or (1,)
        try:
            self.connection = sqlite.connect(self.db_file)
            self.cursor = self.connection.cursor() 
        except : sys.exit("Unable to connect at the sqlite database.")

        # configure connection
        self.connection.text_factory = str
        self.connection.row_factory = sqlite.Row
        sqlite.register_adapter(str,strEncode)

        if init[0]:
            self._initialise()

    def execute(self,query,parm = None):
        try:
            prefix = DeejaydConfig().get("mediadb","db_prefix") + "_"
        except:
            prefix = ""

        query = query.replace("{",prefix).replace("}","") 
        if parm == None:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query,parm)

    def executemany(self,query,parm):
        try:
            prefix = DeejaydConfig().get("mediadb","db_prefix") + "_"
        except:
            prefix = ""

        query = query.replace("{",prefix).replace("}","") 
        self.cursor.executemany(query,parm)

    def close(self):
        self.cursor.close()
        self.connection.close()


def openConnection():
    try: db_type =  DeejaydConfig().get("mediadb","db_type")
    except: raise SystemExit("You do not choose a database.Verify your config file.")

    supportedDatabase = ("sqlite")
    if db_type not in supportedDatabase:
        raise SystemExit("You choose a database which is not supported.Verify your config file.")

    if db_type == "sqlite":
        db_file = DeejaydConfig().get("mediadb","db_file")
        return sqliteDatabase(db_file)

    return None

# vim: ts=4 sw=4 expandtab
