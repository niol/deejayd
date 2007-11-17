# xine.py

import time
from os import path
from twisted.internet import threads
from deejayd.ext import xine
from deejayd.player._base import *
from deejayd.ui import log

class XinePlayer(UnknownPlayer):
    supported_extensions = None

    def __init__(self,db,config):
        self.name = "xine"
        UnknownPlayer.__init__(self,db,config)

        self.__xine_options = {
            "audio": self.config.get("xine", "audio_output"),
            "video": self.config.get("xine", "video_output"),
            "display" : self.config.get("xine", "video_display"),
            "subtitle": self.config.getint("xine", "subtitle_size"),
            }

        try: self.xine = xine.Xine()
        except xine.XineError, err:
            log.err(str(err))
            raise PlayerError
        # set callback
        self.xine.set_eos_callback(self.eos)
        self.xine.set_progress_callback(self.progress)
        # try to load user config file
        config_file = self.config.get("xine", "config_file")
        self.xine.load_config(path.expanduser(config_file))
        # init audio driver
        try: self.xine.audio_init(self.__xine_options["audio"])
        except xine.XineError, err:
            log.err(str(err))
            raise PlayerError(err)

    def eos(self):
        def __play_next(file,detach,delay):
            if delay > 0: time.sleep(delay)
            self.stop(detach)
            self._media_file = file
            self.start_play()
        def __delay_detach(delay):
            time.sleep(delay)
            self.xine.detach()

        new_file = self._source.next(self.options["random"],\
                    self.options["repeat"])
        if new_file == None:
            threads.deferToThread(__delay_detach,0.2)
        elif self._media_file["type"] != new_file["type"]:
            threads.deferToThread(__play_next,new_file,True,0.2)
        else:
            __play_next(new_file,False,0)

    def progress(self,description,percent):
        msg = description
        if percent > 0:
            msg += " : %d percent" % percent
        log.info(msg)

    def init_video_support(self):
        UnknownPlayer.init_video_support(self)
        try: self.xine.set_enum_config_param(\
            "subtitles.separate.subtitle_size",\
            self.__xine_options["subtitle"])
        except xine.XineError:
            log.err("Xine : unable to set subtitle size")

        try: self.xine.video_init()
        except xine.XineError, err:
            log.err(str(err))
            raise PlayerError

    def __attach(self, isvideo):
        try: self.xine.attach( self.__xine_options["video"],
            self.__xine_options["display"], isvideo)
        except xine.XineError:
            log.err("Xine error : "+self.xine.get_error())
            raise PlayerError
        except xine.XineAlreadyAttached: pass

    def start_play(self):
        if not self._media_file: return

        # format correctly the uri
        uri = self._media_file["uri"]
        # For dvd chapter
        if "chapter" in self._media_file.keys() and \
                    self._media_file["chapter"] != -1:
            uri += ".%d" % self._media_file["chapter"]
        # load external subtitle
        if "external_subtitle" in self._media_file and \
                self._media_file["external_subtitle"].startswith("file://"):
            uri += "#subtitle:%s" % self._media_file["external_subtitle"]
            self._media_file["subtitle"] = [{"lang": "none", "ix": -2},\
                                            {"lang": "auto", "ix": -1},\
                                            {"lang": "external", "ix":0}]

        isvideo,fullscreen = 0,0
        if self._media_file["type"] == "video":
            isvideo = 1
            fullscreen = self.options["fullscreen"]

        self.__attach(isvideo)
        try: self.xine.start_playing(uri, isvideo, fullscreen)
        except xine.XineError:
            log.err("Xine error : "+self.xine.get_error())
        else:
            # if video get current audio/subtitle channel
            if self._media_file["type"] == "video":
                if "audio" in self._media_file:
                    self._media_file["audio_idx"] = self.xine.get_alang()
                if "subtitle" in self._media_file:
                    self._media_file["subtitle_idx"] = self.xine.get_slang()
                self.set_fullscreen(self.options["fullscreen"])

    def _change_file(self,new_file):
        if self._media_file == None or new_file == None:
            detach = True
        elif self._media_file["type"] != new_file["type"]:
            detach = True
        else: detach = False

        self.stop(detach)
        self._media_file = new_file
        self.start_play()

    def pause(self):
        if self.get_state() == PLAYER_PLAY:
            self.xine.pause()
        elif self.get_state() == PLAYER_PAUSE:
            self.xine.play()

    def stop(self, detach = True):
        self._media_file = None
        # FIXME : try to remove this one day ...
        self._source.queue_reset()

        self.xine.stop()
        if detach: self.xine.detach()

    def _player_set_alang(self,lang_idx):
        self.xine.set_alang(lang_idx)

    def _player_set_slang(self,lang_idx):
        self.xine.set_slang(lang_idx)

    def _player_get_alang(self):
        return self.xine.get_alang()

    def _player_get_slang(self):
        return self.xine.get_slang()

    def set_fullscreen(self,val):
        try: self.xine.set_fullscreen(val)
        except xine.NotPlayingError: pass

    def get_volume(self):
        return self.xine.get_volume()

    def set_volume(self,vol):
        self.xine.set_volume(vol)

    def get_position(self):
        try: pos = self.xine.get_position()
        except xine.NotPlayingError: return 0
        else: return pos / 1000

    def set_position(self,pos):
        try: self.xine.seek(int(pos * 1000))
        except xine.NotPlayingError: pass
        else:
            # FIXME I need to wait to be sure that the command is executed
            time.sleep(0.2)

    def get_state(self):
        return self.xine.get_status()

    def is_supported_uri(self,uri_type):
        if uri_type == "dvd":
            # test lsdvd  installation
            if not self._is_lsdvd_exists(): return False
        return self.xine.is_supported_input(uri_type)

    def is_supported_format(self,format):
        if self.__class__.supported_extensions == None:
            extensions = self.xine.get_supported_extensions()
            self.__class__.supported_extensions = extensions.split()

        return format.strip(".") in self.__class__.supported_extensions

    def get_video_file_info(self,file):
        try: info = self.xine.get_file_info(file)
        except xine.FileInfoError: return None
        else: return info

    def get_dvd_info(self):
        dvd_info = self._get_dvd_info()
        ix = 0
        for track in dvd_info['track']:
            # get audio channels info
            channels_number = len(track['audio'])
            audio_channels = [{"lang":"none","ix":-2},{"lang":"auto","ix":-1}]
            for ch in range(0,channels_number):
                lang = self.xine.get_audio_lang("dvd://%d"%track['ix'],ch)
                audio_channels.append({'ix':ch, "lang":lang.encode("utf-8")})
            dvd_info['track'][ix]["audio"] = audio_channels

            # get subtitles channels info
            channels_number = len(track['subp'])
            sub_channels = [{"lang":"none","ix":-2},{"lang":"auto","ix":-1}]
            for ch in range(0,channels_number):
                lang = self.xine.get_subtitle_lang("dvd://%d"%track['ix'],ch)
                sub_channels.append({'ix':ch, "lang":lang.encode("utf-8")})
            dvd_info['track'][ix]["subp"] = sub_channels

            ix += 1

        return dvd_info

# vim: ts=4 sw=4 expandtab
