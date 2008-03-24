# Deejayd, a media player daemon
# Copyright (C) 2007-2008 Mickael Royer <mickael.royer@gmail.com>
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

"""
 Class and methods to manage database
"""

from deejayd.ui import log
from deejayd.database import schema
from os import path
import sys

class OperationalError(Exception): pass

class UnknownDatabase:
    connection = None
    cursor = None

    def connect(self):
        raise NotImplementedError

    def execute(self,cur,query,parm = None):
        raise NotImplementedError

    def executemany(self,cur,query,parm):
        raise NotImplementedError

    def get_new_connection(self):
        raise NotImplementedError

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()


class Database(UnknownDatabase):

    def init_db(self):
        for table in schema.db_schema:
            for stmt in self.to_sql(table):
                self.execute(stmt)
        log.info(_("Database structure successfully created."))
        for query in schema.db_init_cmds:
            self.execute(query)
        log.info(_("Initial entries correctly inserted."))

    def verify_database_version(self):
        try:
            self.execute("SELECT value FROM variables\
                WHERE name = 'database_version'", raise_exception = True)
            (db_version,) = self.cursor.fetchone()
            db_version = int(db_version)
        except OperationalError:
            self.init_db()
        else:
            if schema.db_schema_version > db_version:
                log.info(_("The database structure needs to be updated..."))

                base = path.dirname(__file__)
                base_import = "deejayd.database.upgrade"
                i = db_version+1
                while i < schema.db_schema_version+1:
                    db_file = "db_%d" % i
                    try: up = __import__(base_import+"."+db_file, {}, {}, base)
                    except ImportError:
                        err = _("Unable to upgrade database, have to quit")
                        log.err(err, True)
                    up.upgrade(self.cursor)
                    i += 1

                self.connection.commit()
                log.msg(_("The database structure has been updated"))

    #
    # Common MediaDB requests
    #
    def remove_file(self,dir,f,table = "audio_library"):
        query = "DELETE FROM "+table+" WHERE filename = %s AND dir = %s"
        self.execute(query, (f,dir))

    def erase_empty_dir(self, table = "audio_library"):
        # get list of dir
        query = "SELECT dir,filename FROM "+table+" WHERE type='directory'"
        self.execute(query)

        for (dir,filename) in self.cursor.fetchall():
            query = "SELECT COUNT(*) FROM "+table+" WHERE type='file' AND dir\
                LIKE %s"
            self.execute(query,(path.join(dir,filename)+'%%',))
            rs = self.cursor.fetchone()
            if rs == (0,): # remove directory
                query = "DELETE FROM "+table+" WHERE dir = %s AND filename = %s"
                self.execute(query, (dir,filename))

        return True

    def insert_dir(self,new_dir,table = "audio_library"):
        query = "INSERT INTO "+table+" (dir,filename,type)\
                                 VALUES(%s,%s,'directory')"
        self.execute(query, new_dir)

    def remove_dir(self,root,dir,table = "audio_library"):
        query = "DELETE FROM "+table+" WHERE filename = %s AND dir = %s"
        self.execute(query, (dir,root))
        # We also need to erase the content of this directory
        query = "DELETE FROM "+table+" WHERE dir LIKE %s"
        self.execute(query, (path.join(root,dir)+"%%",))

    def insert_dirlink(self, new_dirlink, table="audio_library"):
        query = "INSERT INTO "+table+" (dir,filename,type)\
                                 VALUES(%s,%s,'dirlink')"
        self.execute(query, new_dirlink)

    def remove_dirlink(self, root, dirlink, table="audio_library"):
        query = "DELETE FROM "+table+" WHERE filename = %s AND dir = %s\
                                                           AND type = %s"
        self.execute(query, (dirlink, root, 'dirlink', ))

    def is_dir_exist(self, root, dir, table = "audio_library"):
        query = "SELECT * FROM "+table+" WHERE filename = %s AND dir = %s AND\
            type = 'directory'"
        self.execute(query, (dir,root))

        return len(self.cursor.fetchall())

    def get_dir_info(self,dir,table = "audio_library"):
        query = "SELECT * FROM "+table+" WHERE dir = %s\
                 ORDER BY type,dir,filename"
        self.execute(query,(dir,))

        return self.cursor.fetchall()

    def get_file_info(self,file,table = "audio_library"):
        query = "SELECT * FROM "+table+" WHERE dir = %s AND filename = %s"
        self.execute(query,path.split(file))

        return self.cursor.fetchall()

    def get_files(self,dir,table = "audio_library"):
        query = "SELECT * FROM "+table+" WHERE dir = %s AND type = 'file'\
                 ORDER BY dir,filename"
        self.execute(query,(dir,))

        return self.cursor.fetchall()

    def get_all_files(self,dir,table = "audio_library"):
        query = "SELECT * FROM "+table+" WHERE dir LIKE %s AND type = 'file'\
            ORDER BY dir,filename"
        self.execute(query,(dir+"%%",))

        return self.cursor.fetchall()

    def get_all_dirs(self,dir,table = "audio_library"):
        query = "SELECT * FROM "+table+\
            " WHERE dir LIKE %s AND type='directory' ORDER BY dir,filename"
        self.execute(query,(dir+"%%",))

        return self.cursor.fetchall()

    def get_all_dirlinks(self, dir, table='audio_library'):
        query = "SELECT * FROM "+table+\
            " WHERE dir LIKE %s AND type='dirlink' ORDER BY dir,filename"
        self.execute(query,(dir+"%%",))
        return self.cursor.fetchall()

    #
    # Specific audio library
    #
    def search_audio_library(self,type,content):
        if type != "all":
            query = "SELECT * FROM audio_library WHERE type = 'file' AND "+\
                type+" LIKE %s ORDER BY dir, filename"
            self.execute(query,('%%'+content+'%%',))
        else:
            query = "SELECT * FROM audio_library WHERE type = 'file' AND \
                (genre LIKE %s OR title LIKE %s OR album LIKE %s OR \
                artist LIKE %s) ORDER BY dir, filename"
            self.execute(query,('%%'+content+'%%','%%'+content+'%%',
                '%%'+content+'%%','%%'+content+'%%'))

        return self.cursor.fetchall()

    def find_audio_library(self,type,content):
        query = "SELECT * FROM audio_library WHERE type = 'file' AND "+\
            type+"= %s"
        self.execute(query,(content,))

        return self.cursor.fetchall()

    def insert_audio_file(self,dir,filename,fileInfo):
        query = "INSERT INTO audio_library(type,dir,filename,title,artist,\
            album,genre,date,tracknumber,length,bitrate,replaygain_track_gain,\
            replaygain_track_peak)VALUES \
            ('file',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        self.execute(query, (dir,filename,fileInfo["title"],\
            fileInfo["artist"],fileInfo["album"],fileInfo["genre"],\
            fileInfo["date"], fileInfo["tracknumber"],fileInfo["length"],\
            fileInfo["bitrate"],fileInfo["replaygain_track_gain"],\
            fileInfo["replaygain_track_peak"]))

    def update_audio_file(self,dir,filename,fileInfo):
        query = "UPDATE audio_library SET title=%s,artist=%s,album=%s,genre=%s,\
            date=%s,tracknumber=%s,length=%s,bitrate=%s,\
            replaygain_track_gain=%s,replaygain_track_peak=%s\
            WHERE dir=%s AND filename=%s"
        self.execute(query,(fileInfo["title"],fileInfo["artist"],\
            fileInfo["album"],fileInfo["genre"],fileInfo["date"],\
            fileInfo["tracknumber"],fileInfo["length"],fileInfo["bitrate"],\
            fileInfo["replaygain_track_gain"],\
            fileInfo["replaygain_track_peak"],dir,filename))

    #
    # Video MediaDB specific requests
    #
    def insert_video_file(self,dir,filename,fileInfo):
        query = "INSERT INTO video_library(type,dir,filename,title,length,\
          videowidth,videoheight,subtitle) VALUES ('file',%s,%s,%s,%s,%s,%s,%s)"
        self.execute(query, (dir,filename,\
            fileInfo["title"],fileInfo["length"],fileInfo["videowidth"],\
            fileInfo["videoheight"],fileInfo["subtitle"]))

    def update_video_file(self,dir,filename,fileInfo):
        query = "UPDATE video_library SET title=%s,length=%s,videowidth=%s,\
            videoheight=%s,subtitle=%s WHERE dir=%s AND filename=%s"
        self.execute(query,(fileInfo["title"],fileInfo["length"],\
            fileInfo["videowidth"],fileInfo["videoheight"],\
            fileInfo["subtitle"],dir,filename))

    def update_video_subtitle(self,dir,filename,file_info):
        query = "UPDATE video_library SET subtitle=%s \
            WHERE dir=%s AND filename=%s"
        self.execute(query,(file_info["subtitle"],dir,filename))

    def search_video_library(self,value):
        query = "SELECT * FROM video_library WHERE type = 'file' AND title\
                LIKE %s ORDER BY dir,filename"
        self.execute(query,('%%'+value+'%%',))

        return self.cursor.fetchall()
    #
    # videolist requests
    #
    def get_videolist(self,name):
        query = "SELECT p.position, l.dir, l.filename,\
            l.title, l.length, l.videowidth, l.videoheight, l.subtitle, l.id \
            FROM medialist p LEFT OUTER JOIN video_library l \
            ON p.media_id = l.id WHERE p.name = %s ORDER BY p.position"
        self.execute(query,(name,))
        return self.cursor.fetchall()

    #
    # audiolist requests
    #
    def get_audiolist(self,name):
        query = "SELECT l.id, l.dir, l.filename, l.type, l.title, l.artist,\
            l.album, l.genre, l.tracknumber, l.date, l.length, l.bitrate,\
            l.replaygain_track_gain, replaygain_track_peak, p.position\
            FROM medialist p LEFT OUTER JOIN audio_library l\
            ON p.media_id = l.id WHERE p.name = %s ORDER BY p.position"
        self.execute(query,(name,))
        return self.cursor.fetchall()

    #
    # medialist requests
    #
    def delete_medialist(self,name):
        self.execute("DELETE FROM medialist WHERE name = %s",(name,))
        self.connection.commit()

    def save_medialist(self,content,name):
        values = [(name,s["pos"],s["media_id"]) for s in content]
        query = "INSERT INTO medialist(name,position,media_id)\
            VALUES(%s,%s,%s)"
        self.executemany(query,values)
        self.connection.commit()

    def get_medialist_list(self):
        self.execute("SELECT DISTINCT name FROM medialist ORDER BY name")
        return self.cursor.fetchall()

    #
    # Webradio requests
    #
    def get_webradios(self):
        self.execute("SELECT wid, name, url FROM webradio ORDER BY wid")
        return self.cursor.fetchall()

    def add_webradios(self,values):
        query = "INSERT INTO webradio(wid,name,url)VALUES(%s,%s,%s)"
        self.executemany(query,values)
        self.connection.commit()

    def clear_webradios(self):
        self.execute("DELETE FROM webradio")
        self.connection.commit()

    #
    # Stat requests
    #
    def record_mediadb_stats(self, type):
        if type == "audio":
            # Get the number of songs
            self.execute("SELECT filename FROM audio_library\
                WHERE type = 'file'")
            songs = len(self.cursor.fetchall())
            # Get the number of artist
            self.execute("SELECT DISTINCT artist FROM audio_library\
                WHERE type = 'file'")
            artists = len(self.cursor.fetchall())
            # Get the number of album
            self.execute("SELECT DISTINCT album FROM audio_library\
                WHERE type = 'file'")
            albums = len(self.cursor.fetchall())
            # Get the number of genre
            self.execute("SELECT DISTINCT genre FROM audio_library\
                WHERE type = 'file'")
            genres = len(self.cursor.fetchall())
            values = [(songs,"songs"),(artists,"artists"),(albums,"albums"),\
                      (genres,"genres")]
        elif type == "video":
            # Get the number of video
            self.execute("SELECT DISTINCT filename FROM video_library\
                WHERE type = 'file'")
            values = [(len(self.cursor.fetchall()), "videos")]

        self.executemany("UPDATE stats SET value = %s WHERE name = %s",values)

    def set_update_time(self,type):
        import time
        self.execute("UPDATE stats SET value = %s WHERE name = %s",\
                                        (time.time(),type+"_library_update"))

    def get_update_time(self,type):
        self.execute("SELECT value FROM stats WHERE name = %s",\
                                                    (type+"_library_update",))
        (rs,) =  self.cursor.fetchone()
        return rs

    def get_stats(self):
        self.execute("SELECT * FROM stats")
        return self.cursor.fetchall()

    #
    # State requests
    #
    def set_state(self,values):
        self.executemany("UPDATE variables SET value = %s WHERE name = %s" \
            ,values)
        self.connection.commit()

    def get_state(self,type):
        self.execute("SELECT value FROM variables WHERE name = %s",(type,))
        (rs,) =  self.cursor.fetchone()

        return rs

# vim: ts=4 sw=4 expandtab
