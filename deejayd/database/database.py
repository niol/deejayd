"""
 Class and methods to manage database
"""

from deejayd.ui import log
from os import path
import sys

class databaseExeption: pass

class UnknownDatabase:

    def connect(self):
        raise NotImplementedError

    def execute(self,cur,query,parm = None):
        raise NotImplementedError

    def executemany(self,cur,query,parm):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def get_new_connection(self):
        raise NotImplementedError


class Database(UnknownDatabase):
    database_version = "3"    

    def create_database(self):
        p = path.join(path.dirname(__file__),"sql/database_v%s.sql" % 
                    self.__class__.database_version)
        try: f = open(p)
        except IOError: sys.exit("database structure not found")

        sql_script = f.read()
        self.executescript(sql_script)

        self.connection.commit()
        log.info("Database structure successfully created.")

    def verify_database_version(self):
        # Get current database version
        current_version = int(self.get_state("database_version"))

        new_version = int(self.__class__.database_version)
        if new_version > current_version:
            log.info("The database structure needs to be updated...")

            i = current_version+1
            while i < new_version+1:
                p = path.join(path.dirname(__file__),"sql/update_v%d-v%d.sql" \
                        % (i-1,i))
                try: f = open(p)
                except IOError: 
                    sys.exit("update database file not found")
                sql_script = f.read()
                self.executescript(sql_script)

                i += 1

            self.connection.commit()
            log.msg("The database structure has been updated")

        return True

    #
    # Common MediaDB requests
    #
    def remove_file(self,dir,f,table = "audio_library"):
        query = "DELETE FROM {%s} WHERE filename = ? AND dir = ?" % table
        self.execute(query, (f,dir))

    def erase_empty_dir(self,table = "audio_library"):
        # FIXME : find a better way to do this
        # get list of dir
        query = "SELECT dir,filename FROM {%s} WHERE type='directory'" \
            % (table,)
        self.execute(query)

        for (dir,filename) in self.cursor.fetchall():
            query = "SELECT COUNT(*) FROM {%s} WHERE type='file' AND dir LIKE ?\
                " % table
            self.execute(query,(path.join(dir,filename)+'%%',))
            rs = self.cursor.fetchone()
            if rs == (0,):
                self.remove_dir(dir,filename,table)

        return True

    def insert_dir(self,new_dir,table = "audio_library"):
        query = "INSERT INTO {%s}(dir,filename,type)VALUES(?,?,\
            'directory')" % table
        self.execute(query, new_dir)

    def remove_dir(self,root,dir,table = "audio_library"):
        log.debug("Erase dir (%s,%s) from mediadb" % (root,dir))

        query = "DELETE FROM {%s} WHERE filename = ? AND dir = ?" % table
        self.execute(query, (dir,root))
        # We also need to erase the content of this directory
        query = "DELETE FROM {%s} WHERE dir LIKE ?" % table
        self.execute(query, (path.join(root,dir)+"%%",))

    def get_dir_info(self,dir,table = "audio_library"): 
        query = "SELECT * FROM {%s} WHERE dir = ? ORDER BY type" % (table,)
        self.execute(query,(dir,))

        return self.cursor.fetchall()

    def get_file_info(self,file,table = "audio_library"):
        query = "SELECT * FROM {%s} WHERE dir = ? AND filename = ?" % table
        self.execute(query,path.split(file))

        return self.cursor.fetchall()

    def get_files(self,dir,table = "audio_library"):
        query = "SELECT * FROM {%s} WHERE dir = ? AND type = 'file'" % table
        self.execute(query,(dir,))

        return self.cursor.fetchall()

    def get_all_files(self,dir,table = "audio_library"):
        query = "SELECT * FROM {%s} WHERE dir LIKE ? AND type = 'file' ORDER BY dir,filename" % table
        self.execute(query,(dir+"%%",))

        return self.cursor.fetchall()
    
    def get_all_dirs(self,dir,table = "audio_library"):
        query = "SELECT * FROM {%s} WHERE dir LIKE ? AND type = 'directory'" \
                                                                        % table
        self.execute(query,(dir+"%%",))

        return self.cursor.fetchall()

    #
    # Specific audio library
    #
    def search_audio_library(self,type,content):
        if type != "all":
            query = "SELECT * FROM {audio_library} WHERE type = 'file' AND %s \
                LIKE ?" % (type,)
            self.execute(query,('%%'+content+'%%',))
        else:
            query = "SELECT * FROM {audio_library} WHERE type = 'file' AND \
                (genre LIKE ? OR title LIKE ? OR album LIKE ? OR \
                artist LIKE ?)"
            self.execute(query,('%%'+content+'%%','%%'+content+'%%',
                '%%'+content+'%%','%%'+content+'%%'))

        return self.cursor.fetchall()

    def find_audio_library(self,type,content):
        query = "SELECT * FROM {audio_library} WHERE type = 'file' AND %s = ?" \
                % (type,)
        self.execute(query,(content,))

        return self.cursor.fetchall()

    def insert_audio_file(self,dir,fileInfo):
        query = "INSERT INTO {audio_library}(type,dir,filename,title,artist,\
            album,genre,date,tracknumber,length,bitrate)VALUES \
            ('file',?,?,?,?,?,?,?,?,?,?)"
        self.execute(query, (dir,fileInfo["filename"],fileInfo["title"],\
            fileInfo["artist"],fileInfo["album"],fileInfo["genre"],\
            fileInfo["date"], fileInfo["tracknumber"],fileInfo["length"],\
            fileInfo["bitrate"]))

    def update_audio_file(self,dir,fileInfo):
        query = "UPDATE {audio_library} SET title=?,artist=?,album=?,genre=?,\
            date=?,tracknumber=?,length=?,bitrate=? WHERE dir=? AND filename=?"
        self.execute(query,(fileInfo["title"],fileInfo["artist"],\
            fileInfo["album"],fileInfo["genre"],fileInfo["date"],\
            fileInfo["tracknumber"],fileInfo["length"],fileInfo["bitrate"],\
            dir,fileInfo["filename"]))

    #
    # Video MediaDB specific requests
    #
    def get_last_video_id(self):
        self.execute("SELECT id FROM {video_library} ORDER BY id DESC")
        (lastId,) = self.cursor.fetchone() or (None,)
        return lastId

    def insert_video_file(self,dir,fileInfo):
        query = "INSERT INTO {video_library}(type,dir,filename,id,title,length,\
            videowidth,videoheight,subtitle) VALUES ('file',?,?,?,?,?,?,?,?)"
        self.execute(query, (dir,fileInfo["filename"],fileInfo["id"],\
            fileInfo["title"],fileInfo["length"],fileInfo["videowidth"],\
            fileInfo["videoheight"],fileInfo["subtitle"]))

    def update_video_file(self,dir,fileInfo):
        query = "UPDATE {video_library} SET title=?,length=?,videowidth=?,\
            videoheight=?,subtitle=? WHERE dir=? AND filename=?"
        self.execute(query,(fileInfo["title"],fileInfo["length"],\
            fileInfo["videowidth"],fileInfo["videoheight"],\
            fileInfo["subtitle"],dir,fileInfo["filename"]))

    #
    # Playlist requests
    #
    def get_playlist(self,playlistName):
        query = "SELECT p.dir, p.filename, p.name, p.position, l.dir, \
        l.filename, l.title, l.artist, l.album, l.genre, l.tracknumber, \
        l.date, l.length, l.bitrate FROM {playlist} p LEFT OUTER JOIN \
        {audio_library} l ON p.dir = l.dir AND p.filename = l.filename WHERE \
        p.name = ? ORDER BY p.position"
        self.execute(query,(playlistName,))
        return self.cursor.fetchall()

    def delete_playlist(self,playlistName):
        self.execute("DELETE FROM {playlist} WHERE name = ?",(playlistName,))
        self.connection.commit()

    def save_playlist(self,content,playlistName):
        values = [(playlistName,s["pos"],s["dir"],s["filename"]) \
            for s in content]
        query = "INSERT INTO {playlist}(name,position,dir,filename)\
            VALUES(?,?,?,?)"
        self.executemany(query,values)
        self.connection.commit()

    def get_playlist_list(self):
        self.execute("SELECT DISTINCT name FROM {playlist}")
        return self.cursor.fetchall()

    #
    # Webradio requests
    #
    def get_webradios(self):
        self.execute("SELECT wid, name, url FROM {webradio} ORDER BY wid")
        return self.cursor.fetchall()

    def add_webradios(self,values):
        query = "INSERT INTO {webradio}(wid,name,url)VALUES(?,?,?)"
        self.executemany(query,values)
        self.connection.commit()

    def clear_webradios(self):
        self.execute("DELETE FROM {webradio}")
        self.connection.commit()

    #
    # Stat requests
    #
    def record_mediadb_stats(self):
        # Get the number of songs
        self.execute("SELECT filename FROM {audio_library} WHERE type = 'file'")
        songs = len(self.cursor.fetchall())
        # Get the number of artist
        self.execute("SELECT DISTINCT artist FROM {audio_library} WHERE type = \
            'file'")
        artists = len(self.cursor.fetchall())
        # Get the number of album
        self.execute("SELECT DISTINCT album FROM {audio_library} WHERE type = \
            'file'")
        albums = len(self.cursor.fetchall())

        # record in the database  
        values = [(songs,"songs"),(artists,"artists"),(albums,"albums")]
        self.executemany("UPDATE {stats} SET value = ? WHERE name = ?",values)

    def set_update_time(self,type):
        import time
        self.execute("UPDATE {stats} SET value = ? WHERE name = ?",\
                                        (time.time(),type+"_library_update"))

    def get_update_time(self,type):
        self.execute("SELECT value FROM {stats} WHERE name = ?",\
                                                    (type+"_library_update",))
        (rs,) =  self.cursor.fetchone()
        return rs

    def get_stats(self):
        self.execute("SELECT * FROM {stats}")
        return self.cursor.fetchall()

    #
    # State requests
    #
    def set_state(self,values):
        self.executemany("UPDATE {variables} SET value = ? WHERE name = ?" \
            ,values)
        self.connection.commit()

    def get_state(self,type): 
        self.execute("SELECT value FROM {variables} WHERE name = ?",(type,))
        (rs,) =  self.cursor.fetchone()

        return rs


class DatabaseFactory:
    supported_database = ("sqlite")

    def __init__(self,config):
        self.config = config

        try: self.db_type =  config.get("database","db_type")
        except:
            raise SystemExit(\
                "You do not choose a database.Verify your config file.")
        else:
            if self.db_type not in self.__class__.supported_database:
                raise SystemExit(\
       "You chose a database which is not supported. Verify your config file.")

    def get_db(self):
        if self.db_type == "sqlite":
            db_file = self.config.get("database","db_file")
            try: prefix = self.config.get("database","db_prefix") + "_"
            except NoOptionError: prefix = ""

            from deejayd.database.sqlite import SqliteDatabase
            return SqliteDatabase(db_file,prefix)

        return None

# vim: ts=4 sw=4 expandtab
