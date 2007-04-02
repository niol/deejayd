
import os
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.oggvorbis import OggVorbis

class NotSupportedFormat:pass

class unknownFile:

    def __init__(self,f,player):
        self.player = player
        self.f = f
        self.init = 0
        (path,filename) = os.path.split(f)
        self.info = {"filename": filename}

    def __getitem__(self,infoType):
        pass

    def __getInfo(self):
        pass


class unknownAudioFile(unknownFile):
    supportedTag = ("tracknumber","title","genre","artist","album","date")


class videoFile(unknownFile):
    supportedTag = ("videowidth","length","videoheight")

    def __setitem__(self,key,value):
        if self.init == 0:
            self.__getInfo()
            self.init = 1
        self.info[key] = value

    def __getitem__(self,infoType):
        if self.init == 0:
            self.__getInfo()
            self.init = 1

        if infoType in self.info:
            return self.info[infoType]
        else:
            return ""

    def __getInfo(self):
        self.info["title"] = self.info["filename"]
        videoInfo = self.player.getVideoFileInfo(self.f)
        for t in self.__class__.supportedTag:
            self.info[t] = videoInfo[t]


class mp3File(unknownAudioFile):

    def __getitem__(self,infoType):
        if self.init == 0:
            self.__getInfo()
            self.init = 1

        if infoType in self.info:
            return self.info[infoType]
        else:
            return ""

    def __getInfo(self):
        mp3Info = MP3(self.f,ID3=EasyID3) 
        mp3Info.pprint()
        self.info["bitrate"] = mp3Info.info.bitrate
        self.info["length"] = int(mp3Info.info.length)

        for t in self.__class__.supportedTag:
            try:
                self.info[t] = mp3Info[t][0]
                if self.info[t] is unicode:
                    self.info[t] = self.info[t]
            except:
                self.info[t] = '';

class oggFile(unknownAudioFile):

    def __getitem__(self,infoType):
        if self.init == 0:
            self.__getInfo()
            self.init = 1

        if infoType in self.info:
            return self.info[infoType]
        else:
            return ""

    def __getInfo(self):
        oggInfo = OggVorbis(self.f) 
        oggInfo.pprint()
        self.info["bitrate"] = oggInfo.info.bitrate
        self.info["length"] = int(oggInfo.info.length)

        for t in self.__class__.supportedTag:
            try:
                self.info[t] = oggInfo[t][0]
                if self.info[t] is unicode:
                    self.info[t] = self.info[t]
            except:
                self.info[t] = '';


class fileTag:

    __supportedFormat = None
    __player = None

    def __init__(self,player = None):
        if fileTag.__player == None:
            fileTag.__player = player
        
        if fileTag.__supportedFormat == None and fileTag.__player != None:
            # Find supported format
            fileTag.__supportedFormat = {}

            # mp3
            if fileTag.__player.isSupportedFormat(".mp3"): 
                fileTag.__supportedFormat[".mp3"] = mp3File
                fileTag.__supportedFormat[".mp2"] = mp3File

            # ogg
            if fileTag.__player.isSupportedFormat(".ogg"): 
                fileTag.__supportedFormat[".ogg"] = oggFile

            # video
            for ext in (".avi",".mpeg",".mpg"):
                if fileTag.__player.isSupportedFormat(ext):
                    fileTag.__supportedFormat[ext] = videoFile

    def getFileTag(self,realFile):
        (filename,extension) = os.path.splitext(realFile)
        ext = extension.lower()

        if ext in fileTag.__supportedFormat.keys():
            return fileTag.__supportedFormat[ext](realFile,fileTag.__player)
        else: raise NotSupportedFormat


# vim: ts=4 sw=4 expandtab
