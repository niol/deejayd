
import os
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.oggvorbis import OggVorbis

class NotSupportedFormat:pass

class unknownAudioFile:
    supportedTag = ("tracknumber","title","genre","artist","album","date")

    def __init__(self,f):
        self.f = f
        self.init = 0
        (path,filename) = os.path.split(f)
        self.info = {"filename": filename}

    def __getitem__(self,infoType):
        pass

    def __getInfo(self):
        pass


class mp3File(unknownAudioFile):

    def __init__(self,f):
        unknownAudioFile.__init__(self,f)
        from mutagen.mp3 import MP3
        from mutagen.easyid3 import EasyID3

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

    def __init__(self):
        if fileTag.__supportedFormat == None:
            # Find supported format
            fileTag.__supportedFormat = {}
            import gst

            # mp3
            if gst.registry_get_default().find_plugin("mad") is not None:
                    fileTag.__supportedFormat[".mp3"] = mp3File
                    fileTag.__supportedFormat[".mp2"] = mp3File

            # ogg
            if gst.registry_get_default().find_plugin("vorbis") is not None\
                and gst.registry_get_default().find_plugin("ogg") is not None:
                    fileTag.__supportedFormat[".ogg"] = oggFile

    def getFileTag(self,realFile):
        (filename,extension) = os.path.splitext(realFile)
        ext = extension.lower()

        if ext in fileTag.__supportedFormat.keys():
            return fileTag.__supportedFormat[ext](realFile)
        else: raise NotSupportedFormat


# vim: ts=4 sw=4 expandtab
