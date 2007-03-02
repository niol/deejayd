# -*- coding: utf-8 -*-

import tag
import os, sys, time
from deejayd.ui.config import DeejaydConfig
import database
from twisted.python import log
from twisted.internet import threads

class NotFoundException:pass

class DeejaydFile:

    def __init__(self, library, db, dir):
        self.library = library
        self.db = db
        self.dir = dir

    def insert(self,f):
        realDir = os.path.join(self.library.getRootPath(), self.dir)
        realFile = os.path.join(realDir,f)
        
        try: fileInfo = tag.fileTag().getFileTag(realFile) 
        except tag.NotSupportedFormat: 
            # Not an supported file
            log.msg("%s : format not supported" % (f,))
            return

        self.db.insertFile(self.dir,fileInfo)

    def update(self,f):
        realDir = os.path.join(self.library.getRootPath(), self.dir)
        realFile = os.path.join(realDir,f)
        
        try: fileInfo = tag.fileTag().getFileTag(realFile) 
        except tag.NotSupportedFormat: 
            # Not an supported file
            log.msg("%s : format not supported" % (f,))
            return

        self.db.updateFile(self.dir,fileInfo)

    def remove(self,f):
        seld.db.removeFile(self.dir,f)


class DeejaydDir:

    def __init__(self, library, db = None):
        self.library = library
        self.db = db or self.library.getDB()

    def update(self,dir,lastUpdateTime):
        self.testDir(dir)

        realDir = os.path.join(self.library.getRootPath(), dir)
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
            djFile = DeejaydFile(self.library,self.db,dir)
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

    def testDir(self,dir):
        realDir = os.path.join(self.library.getRootPath(), dir)
        # Test directory existence
        if not os.path.isdir(realDir):
            raise NotFoundException


class DeejaydDB:
    """deejaydDB
    Class to manage the media database
    """
    def __init__(self, db, root_path):
        # init Parms
        self.__updateDBId = 0
        self.__updateEnd = True
        self.__updateError = None

        self.__root_path = root_path

        # Connection to the database
        self.db = db
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
        DeejaydDir(self,db).update(dir,self.lastUpdateTime)
        db.setStat('db_update',time.time())

        # record the change in the database
        db.connection.commit()

        # update stat values
        db.recordMediaDBStat()

    def endUpdate(self, result = True): 
        self.__updateEnd = True
        if result: log.msg("The database has been updated")
        else:
            msg = "Unable to update the database. See log for more information"
            log.err(msg)
            self.__updateError = msg
        return True


    def update(self,dir):
        if self.__updateEnd:
            # First we test the directory
            DeejaydDir(self).testDir(dir)

            self.__updateDBId += 1
            self.d = threads.deferToThread(self.updateDir,dir)
            self.d.pause()

            # Add callback functions
            succ = lambda *x: self.endUpdate()
            self.d.addCallback(succ)
            self.d.addErrback(errorHandler,self)

            self.d.unpause()
            return self.__updateDBId
        
        return 0

    def getStatus(self):
        status = []
        if not self.__updateEnd:
            status.append(("updating_db",self.__updateDBId))
        if self.__updateError:
            status.append(("updating_error",self.__updateError))
            self.__updateError = None

        return status

    def getStats(self):
        return self.db.getMediaDBStat()

    def getState(self,name):
        return self.db.getState(name)

    def setState(self,values):
        self.db.setState(values)

    def close(self):
        self.db.close()

    def getRootPath(self):
        return self.__root_path

    def getDB(self):
        return self.db


def errorHandler(failure,dbClass):
    # Log the exception to debug pb later
    failure.printTraceback()
    dbClass.endUpdate(False)

    return False


# for test only
if __name__ == "__main__":
    djDB = DeejaydDB()

    t = int(time.time())
    djDB.updateDir("")
    print int(time.time()) - t
    djDB.close()

# vim: ts=4 sw=4 expandtab
