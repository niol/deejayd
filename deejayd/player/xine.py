# xine.py

from deejayd.ext import xine
from deejayd.player._base import UnknownPlayer,PLAYER_PLAY,PLAYER_PAUSE,\
                                 PLAYER_STOP
from deejayd.ui import log


class XinePlayer(UnknownPlayer):
    supported_mimetypes = None
    supported_extensions = None

    def __init__(self,db,config):
        self.name = "xine"
        UnknownPlayer.__init__(self,db,config)

        audio_driver = self.config.get("xine", "audio_output")
        self.xine = xine.Xine(audio_driver)
        self.xine.set_eos_callback(self.eos)
        self.xine.set_progress_callback(self.progress)

    def eos(self):
        self.next()

    def progress(self,description,percent):
        msg = description
        if percent > 0:
            msg += " : %d percent" % percent
        log.info(msg)

    def init_video_support(self):
        UnknownPlayer.init_video_support(self)

        # load specific xine config
        try: subtitle_size = self.config.getint("xine", "subtitle_size")
        except: 
            log.err("Unable to read xine.subtitle_size conf parm")
        else:
            try: self.xine.set_enum_config_param(\
                "subtitles.separate.subtitle_size", int(subtitle_size))
            except xine.XineError:
                log.err("Xine : unable to load specific xine config")

        video_driver = self.config.get("xine", "video_output")
        video_display = self.config.get("xine", "video_display")
        self.xine.video_init(video_driver,video_display)

    def start_play(self):
        if not self._media_file: return

        # format correctly the uri
        uri = self._media_file["uri"]
        if "Subtitle" in self._media_file.keys() and \
                self._media_file["Subtitle"].startswith("file://") and \
                self.options["loadsubtitle"]:
                uri += "#subtitle:%s" % self._media_file["Subtitle"]

        isvideo = 0
        if self._media_file["Type"] == "video": isvideo = 1
        try: self.xine.start_playing(uri, isvideo, self.options["fullscreen"])
        except xine.XineError:
            log.err("Xine error : "+self.xine.get_error())
        else: self.set_fullscreen(self.options["fullscreen"])

    def pause(self):
        if self.get_state() == PLAYER_PLAY:
            self.xine.pause()
        elif self.get_state() == PLAYER_PAUSE:
            self.xine.play()

    def stop(self):
        self._media_file = None
        # FIXME : try to remove this one day ...
        self._source.queue_reset()

        self.xine.stop()

    def set_fullscreen(self,val):
        try: self.xine.set_fullscreen(val)
        except xine.NotPlayingError: pass

    def set_subtitle(self,val):
        try: self.xine.set_subtitle(val)
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
            import time
            time.sleep(0.2)
    
    def get_state(self):
        return self.xine.get_status()

    def is_supported_uri(self,uri_type):
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

# vim: ts=4 sw=4 expandtab
