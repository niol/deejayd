# -*- coding: utf-8 -*-
"""
"""

from _util import *
from tag import mp3File, oggFile
import os, sys, time
from deejayd.ui.config import DeejaydConfig
import database


class DeejaydFile:
    root_path =  DeejaydConfig().get("mediadb","music_directory")

    def __init__(self,db,dir):
        self.db = db
        self.dir = dir

    def insert(self,f):
        realDir = os.path.join(self.__class__.root_path,self.dir)
        realFile = os.path.join(realDir,f)
        
        fileInfo = self.__getFileTags(realFile) 
        if fileInfo == None:
            return

        query = "INSERT INTO {library}(type,dir,filename,title,artist,album,genre,date,tracknumber,length,bitrate)VALUES\
                ('file',?,?,?,?,?,?,?,?,?,?)"
        self.db.execute(query, (strEncode(self.dir),strEncode(f),fileInfo["title"],fileInfo["artist"],fileInfo["album"],\
            fileInfo["genre"], fileInfo["date"], fileInfo["tracknumber"],fileInfo["length"],fileInfo["birate"]))

    def update(self,f):
        realDir = os.path.join(self.__class__.root_path,self.dir)
        realFile = os.path.join(realDir,f)
        
        fileInfo = self.__getFileTags(realFile) 
        if fileInfo == None:
            return

        query = "UPDATE {library} SET title=?,artist=?,album=?,genre=?,date=?,tracknumber=?,length=?,bitrate=? WHERE dir=? \
            AND filename=?"
        self.db.execute(query,(fileInfo["title"],fileInfo["artist"],fileInfo["album"],fileInfo["genre"],fileInfo["date"],\
            fileInfo["tracknumber"],fileInfo["length"],fileInfo["birate"],strEncode(self.dir),strEncode(f)))

    def remove(self,f):
        try:
            query = "DELETE FROM {library} WHERE filename = ? AND dir = ?"
            self.db.execute(query, (strEncode(f),strEncode(self.dir)))
        except:
            print "Impossible to delete the file %s : %s from the database" % (self.dir, f)

    # Private functions
    def __getFileTags(self,f):
        realDir = os.path.join(self.__class__.root_path,self.dir)
        (filename,extension) = os.path.splitext(f)
        ext = extension.lower()

        if ext == ".mp3":
            return mp3File(f)
        elif ext == ".ogg":
            return oggFile(f)
        else:
            return None


class DeejaydDir:
    root_path =  DeejaydConfig().get("mediadb","music_directory")

    def __init__(self,db):
        self.db = db

    def update(self,dir,lastUpdateTime):
        realDir = os.path.join(self.__class__.root_path,dir)
        dbRecord = self.__get(dir)

        # First we update the list of directory
        directories = [ os.path.join(dir,d) for d in os.listdir(realDir) \
                if os.path.isdir(os.path.join(realDir,d))]
        for d in [di for (di,t) in dbRecord if t == 'directory']:
            if os.path.isdir(os.path.join(realDir,d)):
                try:
                    if d in directories:
                        directories.remove(d)
                except:
                    print directories
            else:
                # directory do not exist, we erase it
                query = "DELETE FROM {library} WHERE filename = ? AND dir = ?"
                self.db.execute(query, (strEncode(d),strEncode(dir)))
        # Add new diretory
        for d in directories:
            try:
                query = "INSERT INTO {library}(dir,filename,type)VALUES(?,?,'directory')"
                self.db.execute(query, (strEncode(dir),strEncode(d)))
            except:
                print "Impossible to add directory %s" % (d,)

        # Now we update the list of files if necessary
        if int(os.stat(realDir).st_mtime) >= lastUpdateTime:
            files = [ f for f in os.listdir(realDir) if os.path.isfile(os.path.join(realDir,f))]
            djFile = DeejaydFile(self.db,dir)
            for f in [fi for (fi,t) in dbRecord if t == 'file']:
                if os.path.isfile(os.path.join(realDir,f)):
                    djFile.update(f)
                    if f in files:
                        files.remove(f)
                else:
                    djFile.remove(f)
            # Insert new files
            for f in files:
                djFile.insert(f)

        # Finally we update subdirectories
        directories = [ os.path.join(dir,d) for d in os.listdir(realDir) \
                if os.path.isdir(os.path.join(realDir,d))]
        for d in directories:
            self.update(d,lastUpdateTime)

    # Private functions
    def __get(self,dir):
        # First, we encode correctly the name of directory
        dir = strEncode(dir)

        result = []
        try:
            query = "SELECT filename,type FROM {library} WHERE dir = ?"
            self.db.execute(query, (dir,))
            result = [(strDecode(d),t) for (d,t) in self.db.cursor.fetchall()]
        except:
            print "Impossible to get directory '%s' elements in the database" % (dir,)

        return result


class DeejaydDB:
    """deejaydDB

    Class to manage the media database
    """
    supportedDatabase = ('sqlite')
    root_path =  DeejaydConfig().get("mediadb","music_directory")

    def __init__(self):
        try:
            db_type =  DeejaydConfig().get("mediadb","db_type")
        except:
            sys.exit("You do not choose a database.Verify your config file.")

        if db_type in self.__class__.supportedDatabase:
            self.db =  getattr(database,db_type+"Database")()
            self.db.connect()
        else:
            sys.exit("You choose a database which is not supported.Verify your config file.")

    def getDir(self,dir):
        query = "SELECT type,dir,filename,title,artist,album,genre,tracknumber,date,length,bitrate FROM {library} \
            WHERE dir = ? ORDER BY type"
        self.db.execute(query,(strEncode(dir),))
        return [ (t,strDecode(dir),strDecode(fn),strDecode(ti),strDecode(ar),strDecode(al),strDecode(gn),strDecode(tn),\
            strDecode(dt),lg,bt) for (t,dir,fn,ti,ar,al,gn,tn,dt,lg,bt) in self.db.cursor.fetchall()]

    def search(self,type,pattern):
        pass

    def update(self,dir):
        self.__getUpdateTime()
        DeejaydDir(self.db).update(dir,self.lastUpdateTime)
        self.__setUpdateTime()

        # record the change in the database
        self.db.connection.commit()

    def close(self):
        self.db.close()

    # Private functions
    def __getUpdateTime(self):
        self.db.execute("SELECT value FROM {stat} WHERE name = 'last_updatedb_time'")
        (self.lastUpdateTime,) = self.db.cursor.fetchone()

    def __setUpdateTime(self):
        t = time.time()
        self.db.execute("UPDATE {stat} SET value = %d WHERE name = 'last_updatedb_time'" \
                    % (int(t),))
        self.db.connection.commit()


# for test only
if __name__ == "__main__":
    djDB = DeejaydDB()

    t = int(time.time())
    djDB.update("")
    print int(time.time()) - t
    djDB.getDir("")

    djDB.close()

# vim: ts=4 sw=4 expandtab
