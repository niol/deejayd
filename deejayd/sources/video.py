
from os import path
from deejayd.mediadb.deejaydDB import NotFoundException
from deejayd.sources.unknown import *

class Video(UnknownSource):

    def __init__(self,library):
        UnknownSource.__init__(self,library,0)
        self.rootPath = library.getVideoRootPath()

    def addVideoFiles(self,files):
        initPos = len(self.sourceContent)
        oldContent = self.sourceContent[initPos:len(self.sourceContent)]
        self.sourceContent = self.sourceContent[0:initPos]

        i = 0
        for f in files:
            pos = initPos+i
            self.sourceContent.append({"dir":f[0],"Title":f[4],"filename":f[1],\
                "Pos":pos,"Id":f[2],"uri":"file://"+path.join(self.rootPath,\
                path.join(f[0],f[1])),"Time":f[5],"Res":f[6]})
            i += 1

        for f in oldContent:
            f["Pos"] = initPos+i
            i += 1

        self.sourceContent.extend(oldContent)
        self.sourceId += len(files)

    def save(self):pass


class VideoSource(UnknownSourceManagement):

    def __init__(self, player, djDB):
        UnknownSourceManagement.__init__(self,player,djDB)

        # Init parms
        self.sourceName = "video"
        self.currentItem = None
        self.currentSource = Video(djDB)
        self.__currentDir = ""

    def setDirectory(self,dir):
        self.currentSource.clear()
        try: videoList = self.djDB.getVideoFiles(dir)
        except NotFoundException: videoList = []

        self.currentSource.addVideoFiles(videoList)
        self.__currentDir = dir

    def getCurrentDir(self):
        return self.__currentDir

    def getStatus(self):
        return [('video_dir',self.__currentDir)]

# vim: ts=4 sw=4 expandtab
