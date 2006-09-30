# -*- coding: utf-8 -*-
"""
"""

from tag import mp3File, oggFile
import os, sys, time
from deejayd.ui.config import DeejaydConfig
import database

from twisted.internet import threads

class NotFoundException:pass

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
        self.db.execute(query, (self.dir,f,fileInfo["title"],fileInfo["artist"],fileInfo["album"],\
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
            fileInfo["tracknumber"],fileInfo["length"],fileInfo["birate"],self.dir,f))

    def remove(self,f):
        query = "DELETE FROM {library} WHERE filename = ? AND dir = ?"
        self.db.execute(query, (f,self.dir))

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
                if d in directories:
                    directories.remove(d)
            else:
                # directory do not exist, we erase it
                query = "DELETE FROM {library} WHERE filename = ? AND dir = ?"
                self.db.execute(query, (d,dir))
                # after we erase all this content
                query = "DELETE FROM {library} WHERE dir LIKE ?"
                self.db.execute(query, (os.path.join(d,dir)+"%%",))
        # Add new diretory
        newDir = [(dir,d) for d in directories]
        if len(newDir) != 0:
            query = "INSERT INTO {library}(dir,filename,type)VALUES(?,?,'directory')"
            self.db.executemany(query, newDir)

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
        newDir = [os.path.join(dir,d) for (dir,d) in newDir]
        for d in directories:
            if d in newDir: self.update(d,0)
            else: self.update(d,lastUpdateTime)

    # Private functions
    def __get(self,dir):
        query = "SELECT filename,type FROM {library} WHERE dir = ?"
        self.db.execute(query, (dir,))

        return self.db.cursor.fetchall()


class DeejaydDB:
    """deejaydDB

    Class to manage the media database
    """
    supportedDatabase = ('sqlite')

    def __init__(self):
        # init Parms
        self.__updateDBId = 0
        self.__updateEnd = True

        # Connection to the database
        self.db = database.openConnection()
        self.db.connect()

    def getDir(self,dir):
        query = "SELECT * FROM {library} WHERE dir = ? ORDER BY type"
        self.db.execute(query,(dir,))

        rs = self.db.cursor.fetchall()
        if len(rs) == 0:
            # nothing found for this directory
            raise NotFoundException

        return rs

    def getFile(self,file):
        (dir,filename) = os.path.split(file)
        query = "SELECT * FROM {library} WHERE dir = ? AND filename = ?"
        self.db.execute(query,(dir,filename))

        rs = self.db.cursor.fetchall()
        if len(rs) == 0:
            # nothing found for this directory
            raise NotFoundException

        return rs

    def getAll(self,dir):
        query = "SELECT * FROM {library} WHERE dir LIKE ? AND TYPE = 'file' ORDER BY dir"
        self.db.execute(query,(dir+'%%',))

        rs = self.db.cursor.fetchall()
        if len(rs) == 0:
            # nothing found for this directory
            raise NotFoundException

        return rs

    def search(self,type,content):
        acceptedType = ('title','genre','filename','artist','album')
        if type not in acceptedType:
            raise NotFoundException

        query = "SELECT * FROM {library} WHERE type = 'file' AND %s LIKE ?" % (type,)
        self.db.execute(query,('%%'+content+'%%',))
        return self.db.cursor.fetchall()

    def find(self,type,content):
        acceptedType = ('title','genre','filename','artist','album')
        if type not in acceptedType:
            raise NotFoundException

        query = "SELECT * FROM {library} WHERE type = 'file' AND %s = ?" % (type,)
        self.db.execute(query,(content,))
        return self.db.cursor.fetchall()

    def updateDir(self,dir):
        db = database.openConnection()
        db.connect()
        self.__updateEnd = False

        self.lastUpdateTime = db.getStat('db_update')
        DeejaydDir(db).update(dir,self.lastUpdateTime)
        db.setStat('db_update',time.time())

        # record the change in the database
        db.connection.commit()

        # update stat values
        db.recordMediaDBStat()

    def endUpdate(self): 
        self.__updateEnd = True

    def update(self,dir):
        if self.__updateEnd:
            self.__updateDBId += 1
            self.d = threads.deferToThread(self.updateDir,dir)
            self.d.pause()

            # Add callback functions
            succ = lambda *x: self.endUpdate()
            err = lambda *x: self.error("Unable to update the database")
            self.d.addCallback(succ)
            self.d.addErrback(err)

            self.d.unpause()
            return self.__updateDBId
        
        return 0

    def getStatus(self):
        status = []
        if not self.__updateEnd:
            status.append(("updating_db",self.__updateDBId))

        return status

    def getStats(self):
        return self.db.getMediaDBStat()

    def close(self):
        self.db.close()

    def error(self,err):
        print err


# for test only
if __name__ == "__main__":
    djDB = DeejaydDB()

    t = int(time.time())
    djDB.updateDir("")
    print int(time.time()) - t
    djDB.close()

# vim: ts=4 sw=4 expandtab
