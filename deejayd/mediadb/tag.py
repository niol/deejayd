
from _util import *
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.oggvorbis import OggVorbis


class unknownAudioFile:
    supportedTag = ("tracknumber","title","genre","artist","album","date")

    def __init__(self,f):
        self.f = f
        self.init = 0
        self.info = {}

    def __getitem__(self,infoType):
        pass

    def __getInfo(self):
        pass


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
        self.info["length"] = mp3Info.info.length

        for t in self.__class__.supportedTag:
            try:
                self.info[t] = mp3Info[t][0]
                if self.info[t] is unicode:
                    self.info[t] = strEncode(self.info[t])
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
        self.info["length"] = oggInfo.info.length

        for t in self.__class__.supportedTag:
            try:
                self.info[t] = oggInfo[t][0]
                if self.info[t] is unicode:
                    self.info[t] = strEncode(self.info[t])
            except:
                self.info[t] = '';


# vim: ts=4 sw=4 expandtab
