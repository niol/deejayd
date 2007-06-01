# xine.py

import sys
from deejayd.ext import xine

from deejayd.player.unknown import UnknownPlayer
from deejayd.ui import log

PLAYER_PLAY = "play"
PLAYER_PAUSE = "pause"
PLAYER_STOP = "stop"

class XinePlayer(UnknownPlayer):
    supported_mimetypes = None
    supported_extensions = None

    def __init__(self,db,config):
        UnknownPlayer.__init__(self,db,config)
        self.xine = xine.Xine("alsa")
        self.xine.set_eos_callback(self.eos)
        self.xine.set_progress_callback(self.progress)

    def eos(self):
        self.next()

    def progress(self,description,percent):
        msg = description
        if percent > 0:
            msg += " : %d percent" % percent
        log.info(msg)

    def initVideoSupport(self):
        UnknownPlayer.initVideoSupport(self)
        self._videoSupport = True
        self.xine.video_init("Xv",":0.0")

    def setURI(self,uri):
        self._uri = uri

    def startPlay(self,init = True):
        if init: UnknownPlayer.startPlay(self)

        self.setState(PLAYER_PLAY)
        self.startXine()

    def startXine(self):
        isvideo = 0
        if self._playingSourceName == "video":
            isvideo = 1
        try: self.xine.start_playing(self._uri,isvideo)
        except xine.StartPlayingError:
            self.setState(PLAYER_STOP)
            log.err("Xine error : "+self.xine.get_error())

    def pause(self):
        if self.getState() == PLAYER_PLAY:
            self.xine.pause()
            self.setState(PLAYER_PAUSE)
        elif self.getState() == PLAYER_PAUSE:
            self.xine.play()
            self.setState(PLAYER_PLAY)

    def stop(self):
        self.setState(PLAYER_STOP)
        # Reset the queue
        self._queue.reset()
        self.xine.stop()

    def setFullscreen(self,val):
        try: self.xine.set_fullscreen(val)
        except xine.NotPlayingError: pass

    def setSubtitle(self,val):
        pass

    def getVolume(self):
        return self.xine.get_volume()

    def setVolume(self,vol):
        self.xine.set_volume(vol)

    def getPosition(self):
        try: pos = self.xine.get_position()
        except xine.NotPlayingError: return 0
        else: return pos / 1000

    def setPosition(self,pos):
        try: self.xine.seek(int(pos * 1000))
        except xine.NotPlayingError: pass 
        else:
            # FIXME I need to wait to be sure that the command is executed
            import time
            time.sleep(0.2)

    #
    # file format info
    #
    def webradioSupport(self):
        if self.__class__.supported_mimetypes == None:
            mime_types = self.xine.get_supported_mimetypes()
            mime_types = mime_types.split(";")
            self.__class__.supported_mimetypes = [ m.split(":")[0] for m in \
                mime_types]

        return "audio/mpegurl" in self.__class__.supported_mimetypes

    def isSupportedFormat(self,format):
        if self.__class__.supported_extensions == None:
            extensions = self.xine.get_supported_extensions()
            self.__class__.supported_extensions = extensions.split()

        return format.strip(".") in self.__class__.supported_extensions

    def getVideoFileInfo(self,file):
        try: info = self.xine.get_file_info(file)
        except xine.FileInfoError: return None
        else: return info

# vim: ts=4 sw=4 expandtab
