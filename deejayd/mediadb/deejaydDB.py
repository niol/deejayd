# -*- coding: utf-8 -*-

import tag
import os, sys, time
import database
from twisted.python import log
from twisted.internet import threads

class NotFoundException:pass

class DeejaydAudioFile:

    def __init__(self,db,player,dir,root_path):
        self.db = db
        self.dir = dir
        self.player = player
        self.root_path = root_path
        self.update_function = self.db.updateAudioFile
        self.insert_function = self.db.insertAudioFile
        self.file_type = "audio"

    def insert(self,f):
        file_info = self._get_file_info(f)
        if file_info:
            self.insert_function(self.dir,file_info)

    def update(self,f):
        file_info = self._get_file_info(f)
        if file_info:
            self.update_function(self.dir,file_info)

    def remove(self,f):
        self.db.removeFile(self.dir,f)

    def _get_file_info(self,f):
        real_dir = os.path.join(self.root_path, self.dir)
        real_file = os.path.join(real_dir,f)
        
        try: file_info = tag.fileTag(self.player).getFileTag(real_file,\
            self.file_type) 
        except tag.NotSupportedFormat: 
            # Not an supported file
            log.msg("%s : %s format not supported" % (f,self.file_type))
            return None
        else: return file_info


class DeejaydVideoFile(DeejaydAudioFile):

    def __init__(self,db,player,dir,root_path = None):
        DeejaydAudioFile.__init__(self,db,player,dir,root_path)

        self.update_function = self.db.updateVideoFile
        self.insert_function = self.db.insertVideoFile
        self.__id = self.db.getLastVideoId() or 0 
        self.file_type = "video"

    def insert(self,f):
        file_info = self._get_file_info(f)
        if file_info:
            file_info["id"] = self.__get_next_id()
            self.insert_function(self.dir,file_info)

    def __get_next_id(self):
        self.__id += 1
        return self.__id


class DeejaydDir:

    def __init__(self, library, db = None, type = "audio"):
        self.db = db or library.getDB()
        self.player = library.getPlayer()
        if type =="audio":
            self.table = "audio_library"
            self.rootPath = library.getAudioRootPath()
            self.fileClass = DeejaydAudioFile
        elif type =="video":
            self.table = "video_library"
            self.rootPath = library.getVideoRootPath()
            self.fileClass = DeejaydVideoFile

    def update(self,dir,lastUpdateTime):
        self.testDir(dir)

        realDir = os.path.join(self.rootPath, dir)
        dbRecord = self.db.getDirContent(dir,self.table)
        # First we update the list of directory
        directories = [ os.path.join(dir,d) for d in os.listdir(realDir) \
                if os.path.isdir(os.path.join(realDir,d))]
        for d in [di for (di,t) in dbRecord if t == 'directory']:
            if os.path.isdir(os.path.join(realDir,d)):
                if d in directories:
                    directories.remove(d)
            else:
                # directory do not exist, we erase it
                self.db.eraseDir(dir,d,self.table)
        # Add new diretory
        newDir = [(dir,d) for d in directories]
        if len(newDir) != 0: self.db.insertDir(newDir,self.table)

        # Now we update the list of files if necessary
        if int(os.stat(realDir).st_mtime) >= lastUpdateTime:
            files = [ f for f in os.listdir(realDir) 
                if os.path.isfile(os.path.join(realDir,f))]
            djFile = self.fileClass(self.db,self.player,dir,self.rootPath)
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
        realDir = os.path.join(self.rootPath, dir)
        # Test directory existence
        if not os.path.isdir(realDir):
            raise NotFoundException


class DeejaydDB:
    """deejaydDB
    Class to manage the media database
    """
    def __init__(self, db, audio_path, video_path = None):
        # init Parms
        self.__updateDBId = 0
        self.__updateEnd = True
        self.__updateError = None
        self.__dbUpdate = None

        self.__audio_path = audio_path
        self.__video_path = video_path

        self.player = None

        # Connection to the database
        self.db = db
        self.db.connect()

    def getDir(self,dir, type = "audio"):
        rs = self.db.getDirInfo(dir,type)
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

    def getVideoFiles(self,dir):
        rs = self.db.getVideoFiles(dir)
        if len(rs) == 0:
            raise NotFoundException

        return rs

    def getAll(self,dir):
        rs = self.db.getAllFile(dir)
        if len(rs) == 0 and dir != "":
            # nothing found for this directory
            raise NotFoundException

        return rs

    def search(self,type,content):
        acceptedType = ('all','title','genre','filename','artist','album')
        if type not in acceptedType:
            raise NotFoundException

        return self.db.searchInAudioMediaDB(type,content)

    def find(self,type,content):
        acceptedType = ('title','genre','filename','artist','album')
        if type not in acceptedType:
            raise NotFoundException

        return self.db.findInAudioMediaDB(type,content)

    def updateDir(self,dir):
        self.__dbUpdate = self.db.getNewConnection()
        self.__dbUpdate.connect()
        self.__updateEnd = False

        self.lastUpdateTime = self.__dbUpdate.getStat('db_update')
        # Update video library
        if self.__video_path:
            DeejaydDir(self,self.__dbUpdate,"video").update(dir,self.\
                lastUpdateTime)
        # Update audio library
        DeejaydDir(self,self.__dbUpdate).update(dir,self.lastUpdateTime)

        # Remove empty dir
        self.__dbUpdate.eraseEmptyDir("audio_library")
        self.__dbUpdate.eraseEmptyDir("video_library")
        # record the change in the database
        self.__dbUpdate.connection.commit()

        # update stat values
        self.__dbUpdate.setStat('db_update',time.time())
        self.__dbUpdate.recordMediaDBStat()
        # close the connextion
        self.__dbUpdate.close()
        self.__dbUpdate = None

    def endUpdate(self, result = True): 
        self.__updateEnd = True
        if result: log.msg("The database has been updated")
        else:
            msg = "Unable to update the database. See log for more information"
            log.err(msg)
            self.__updateError = msg
            # close opened connection if necessary
            try:
                self.__dbUpdate.close()
                self.__dbUpdate = None
            except: pass
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

    def getAudioRootPath(self):
        return self.__audio_path

    def getVideoRootPath(self):
        return self.__video_path

    def getDB(self):
        return self.db

    def setPlayer(self,player):
        self.player = player

    def getPlayer(self):
        return self.player

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
