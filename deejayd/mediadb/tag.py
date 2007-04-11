
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
        def format_title(f):
            (filename,ext) = os.path.splitext(f)
            title = filename.replace(".", " ")
            title = title.replace("_", " ")

            return title.title()
        
        # Try to find a subtitle (same name with a srt extension)
        (base_path,ext) = os.path.splitext(self.f)
        if os.path.isfile(base_path+".srt"):
            self.info["subtitle"] = "file://" + base_path + ".srt"
        else: self.info["subtitle"] = ""

        self.info["title"] = format_title(self.info["filename"])
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

    __supportedAudioFormat = None
    __supportedVideoFormat = None
    __player = None

    def __init__(self,player = None):
        if fileTag.__player == None:
            fileTag.__player = player
        
        if fileTag.__supportedAudioFormat == None or \
            fileTag.__supportedVideoFormat == None and fileTag.__player != None:
            # Find supported format
            fileTag.__supportedAudioFormat = {}
            fileTag.__supportedVideoFormat = {}

            # mp3
            if fileTag.__player.isSupportedFormat(".mp3"): 
                fileTag.__supportedAudioFormat[".mp3"] = mp3File
                fileTag.__supportedAudioFormat[".mp2"] = mp3File

            # ogg
            if fileTag.__player.isSupportedFormat(".ogg"): 
                fileTag.__supportedAudioFormat[".ogg"] = oggFile

            # video
            for ext in (".avi",".mpeg",".mpg"):
                if fileTag.__player.isSupportedFormat(ext):
                    fileTag.__supportedVideoFormat[ext] = videoFile

    def getFileTag(self,realFile,type):
        (filename,extension) = os.path.splitext(realFile)
        ext = extension.lower()

        if type == "audio":
            if ext in fileTag.__supportedAudioFormat.keys():
                return fileTag.__supportedAudioFormat[ext](realFile,\
                    fileTag.__player)
            else: raise NotSupportedFormat
        elif type == "video":
            if ext in fileTag.__supportedVideoFormat.keys():
                return fileTag.__supportedVideoFormat[ext](realFile,\
                    fileTag.__player)
            else: raise NotSupportedFormat


# vim: ts=4 sw=4 expandtab
