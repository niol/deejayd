# xine.py

from deejayd.ext import xine
from deejayd.player import UnknownPlayer,PLAYER_PLAY,PLAYER_PAUSE,PLAYER_STOP
from deejayd.ui import log


class XinePlayer(UnknownPlayer):
    supported_mimetypes = None
    supported_extensions = None

    def __init__(self,db,config):
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

        video_driver = self.config.get("xine", "video_output")
        video_display = self.config.get("xine", "video_display")
        self.xine.video_init(video_driver,video_display)
        self._video_support = True

    def set_uri(self,song):
        if song:
            uri = song["uri"]
            if "Subtitle" in song.keys() and \
                song["Subtitle"].startswith("file://") and self._loadsubtitle:
                uri += "#subtitle:%s" % song["Subtitle"]
            self._uri = uri
        else: self._uri = ""

    def start_play(self):
        UnknownPlayer.start_play(self)

        self.set_state(PLAYER_PLAY)
        self.start_xine()

    def start_xine(self):
        isvideo = 0
        if self._playing_source_name == "video": isvideo = 1
        try: self.xine.start_playing(self._uri,isvideo,self._fullscreen)
        except xine.StartPlayingError:
            self.set_state(PLAYER_STOP)
            log.err("Xine error : "+self.xine.get_error())
        else: self.set_fullscreen(self._fullscreen)

    def pause(self):
        if self.get_state() == PLAYER_PLAY:
            self.xine.pause()
            self.set_state(PLAYER_PAUSE)
        elif self.get_state() == PLAYER_PAUSE:
            self.xine.play()
            self.set_state(PLAYER_PLAY)

    def stop(self):
        self.set_state(PLAYER_STOP)
        # Reset the queue
        self._queue.reset()
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

    #
    # file format info
    #
    def webradio_support(self):
        if self.__class__.supported_mimetypes == None:
            mime_types = self.xine.get_supported_mimetypes()
            mime_types = mime_types.split(";")
            self.__class__.supported_mimetypes = [ m.split(":")[0] for m in \
                mime_types]

        return "audio/mpegurl" in self.__class__.supported_mimetypes

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
