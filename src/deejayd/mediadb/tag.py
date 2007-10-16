
import os
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.oggvorbis import OggVorbis

class NotSupportedFormat:pass
class UnknownException:pass

class UnknownFile:

    def __init__(self,f,player):
        self.player = player
        self.f = f
        (path,filename) = os.path.split(f)
        self.info = {"filename": filename}

    def __getitem__(self,key):
        raise NotImplementedError

    def load_file_info(self):
        raise NotImplementedError


class UnknownAudioFile(UnknownFile):
    supported_tag = ("tracknumber","title","genre","artist","album","date")


class VideoFile(UnknownFile):
    supported_tag = ("videowidth","length","videoheight")

    def __setitem__(self,key,value):
        self.info[key] = value

    def __getitem__(self,key):
        if key in self.info: return self.info[key]
        else: return ""

    def load_file_info(self):
        def format_title(f):
            (filename,ext) = os.path.splitext(f)
            title = filename.replace(".", " ")
            title = title.replace("_", " ")

            return title.title()

        self.load_subtitle()
        self.info["title"] = format_title(self.info["filename"])
        video_info = self.player.get_video_file_info(self.f)
        for t in self.__class__.supported_tag:
            try: self.info[t] = video_info[t]
            except: raise UnknownException

    def load_subtitle(self):
        # Try to find a subtitle (same name with a srt/sub extension)
        (base_path,ext) = os.path.splitext(self.f)
        sub = ""
        for ext_type in (".srt",".sub"):
            if os.path.isfile(base_path + ext_type):
                sub = "file://" + base_path + ext_type
                break
        self.info["subtitle"] = sub


class Mp3File(UnknownAudioFile):

    def __getitem__(self,key):
        if key in self.info: return self.info[key]
        else: return ""

    def load_file_info(self):
        mp3_info = MP3(self.f,ID3=EasyID3)
        self.info["bitrate"] = int(mp3_info.info.bitrate)
        self.info["length"] = int(mp3_info.info.length)

        for t in self.__class__.supported_tag:
            try: self.info[t] = mp3_info[t][0]
            except: self.info[t] = '';


class OggFile(UnknownAudioFile):

    def __getitem__(self,key):
        if key in self.info: return self.info[key]
        else: return ""

    def load_file_info(self):
        ogg_info = OggVorbis(self.f)
        self.info["bitrate"] = int(ogg_info.info.bitrate)
        self.info["length"] = int(ogg_info.info.length)

        for t in self.__class__.supported_tag:
            try: self.info[t] = ogg_info[t][0]
            except: self.info[t] = '';


class FileTagFactory:

    supported_audio_format = None
    supported_video_format = None
    player = None

    def __init__(self,player = None):
        if self.__class__.player == None:
            self.__class__.player = player

        if self.__class__.supported_audio_format == None or \
                self.__class__.supported_video_format == None and \
                self.__class__.player != None:
            self.__class__.supported_audio_format = {}
            self.__class__.supported_video_format = {}
            # mp3
            if self.__class__.player.is_supported_format(".mp3"):
                self.__class__.supported_audio_format[".mp3"] = Mp3File
                self.__class__.supported_audio_format[".mp2"] = Mp3File

            # ogg
            if self.__class__.player.is_supported_format(".ogg"):
                self.__class__.supported_audio_format[".ogg"] = OggFile

            # video
            for ext in (".avi",".mpeg",".mpg"):
                if self.__class__.player.is_supported_format(ext):
                    self.__class__.supported_video_format[ext] = VideoFile

    def get_file_tag_object(self,real_file,library_type = "audio"):
        supported_format = library_type == "audio" and \
                    self.__class__.supported_audio_format or\
                    self.__class__.supported_video_format

        (filename,extension) = os.path.splitext(real_file)
        ext = extension.lower()

        if ext in supported_format.keys():
            return supported_format[ext](real_file,\
                    self.__class__.player)
        else: raise NotSupportedFormat


# vim: ts=4 sw=4 expandtab
