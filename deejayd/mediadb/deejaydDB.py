# -*- coding: utf-8 -*-

import tag
import os, sys, time
from deejayd.ui.config import DeejaydConfig
import database
from twisted.python import log
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
        
        try: fileInfo = tag.getFileTag(realFile) 
        except tag.NotSupportedFormat: 
            # Not an supported file
            log.msg("%s : format not supported" % (f,))
            return

        self.db.insertFile(self.dir,fileInfo)

    def update(self,f):
        realDir = os.path.join(self.__class__.root_path,self.dir)
        realFile = os.path.join(realDir,f)
        
        try: fileInfo = tag.getFileTag(realFile) 
        except tag.NotSupportedFormat: 
            # Not an supported file
            log.msg("%s : format not supported" % (f,))
            return

        self.db.updateFile(self.dir,fileInfo)

    def remove(self,f):
        seld.db.removeFile(self.dir,f)


class DeejaydDir:
    root_path =  DeejaydConfig().get("mediadb","music_directory")

    def __init__(self,db):
        self.db = db

    def update(self,dir,lastUpdateTime):
        realDir = os.path.join(self.__class__.root_path,dir)
        # Test directory existence
        if not os.path.isdir(realDir):
            raise NotFoundException

        dbRecord = self.db.getDirContent(dir)
        # First we update the list of directory
        directories = [ os.path.join(dir,d) for d in os.listdir(realDir) \
                if os.path.isdir(os.path.join(realDir,d))]
        for d in [di for (di,t) in dbRecord if t == 'directory']:
            if os.path.isdir(os.path.join(realDir,d)):
                if d in directories:
                    directories.remove(d)
            else:
                # directory do not exist, we erase it
                self.db.eraseDir(dir,d)
        # Add new diretory
        newDir = [(dir,d) for d in directories]
        if len(newDir) != 0: self.db.insertDir(newDir)

        # Now we update the list of files if necessary
        if int(os.stat(realDir).st_mtime) >= lastUpdateTime:
            files = [ f for f in os.listdir(realDir) 
                if os.path.isfile(os.path.join(realDir,f))]
            djFile = DeejaydFile(self.db,dir)
            for f in [fi for (fi,t) in dbRecord if t == 'file']:
                if os.path.isfile(os.path.join(realDir,f)):
                    djFile.update(f)
                    if f in files: files.remove(f)
                else: djFile.remove(f)
            # Insert new files
            for f in files: djFile.insert(f)

        # Finally we update subdirectories
        directories = [ os.path.join(dir,d) for d in os.listdir(realDir) \
                if os.path.isdir(os.path.join(realDir,d))]
        newDir = [os.path.join(dir,d) for (dir,d) in newDir]
        for d in directories:
            if d in newDir: self.update(d,0)
            else: self.update(d,lastUpdateTime)


class DeejaydDB:
    """deejaydDB
    Class to manage the media database
    """
    def __init__(self):
        # init Parms
        self.__updateDBId = 0
        self.__updateEnd = True

        # Connection to the database
        self.db = database.openConnection()
        self.db.connect()

    def getDir(self,dir):
        rs = self.db.getDirInfo(dir)
        if len(rs) == 0 and dir != "":
            # nothing found for this directory
            raise NotFoundException
        return rs

    def getFile(self,file):
        rs = self.db.getFileInfo(file)
        if len(rs) == 0:
            # this file is not found
            raise NotFoundException

        return rs

    def getAll(self,dir):
        rs = self.db.getAllFile(dir)
        if len(rs) == 0:
            # nothing found for this directory
            raise NotFoundException

        return rs

    def search(self,type,content):
        acceptedType = ('all','title','genre','filename','artist','album')
        if type not in acceptedType:
            raise NotFoundException

        return self.db.searchInMediaDB(type,content)

    def find(self,type,content):
        acceptedType = ('title','genre','filename','artist','album')
        if type not in acceptedType:
            raise NotFoundException

        return self.db.findInMediaDB(type,content)

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
        log.msg("The database has been updated")

    def update(self,dir):
        if self.__updateEnd:
            self.__updateDBId += 1
            self.d = threads.deferToThread(self.updateDir,dir)
            self.d.pause()

            # Add callback functions
            succ = lambda *x: self.endUpdate()
            self.d.addCallback(succ)
            self.d.addErrback(errorHandler)

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


def errorHandler(failure):
    #failure.printTraceback()
    if failure.check(deejayd.mediadb.deejaydDB.NotFoundException):
        print("true")
        log.err("Updated directory not found")
    else:
        print("false")
        log.err("Un to update the database")
    failure.raiseException()


# for test only
if __name__ == "__main__":
    djDB = DeejaydDB()

    t = int(time.time())
    djDB.updateDir("")
    print int(time.time()) - t
    djDB.close()

# vim: ts=4 sw=4 expandtab
