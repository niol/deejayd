# gstreamer.py

import sys
import time
from deejayd.ext import xlibhelper
from deejayd.ext import xine

from deejayd.player.unknown import unknownPlayer
from deejayd.ui import log

PLAYER_PLAY = "play"
PLAYER_PAUSE = "pause"
PLAYER_STOP = "stop"

class XinePlayer(unknownPlayer):

    def __init__(self,db,config):
        unknownPlayer.__init__(self,db,config)
        self.xine = xine.Xine("alsa")
        self.xine.set_eos_callback(self.eos)
        self.xine.set_progress_callback(self.progress)

    def eos(self):
        self.next()

    def progress(self,percent):
        log.info("Buffering, Percent : %d" % percent)

    def initVideoSupport(self):
        unknownPlayer.initVideoSupport(self)
        self._videoSupport = True
        self.xine.video_init("Xv",":0.0")

    def setURI(self,uri):
        self._uri = uri

    def startPlay(self,init = True):
        if init: unknownPlayer.startPlay(self)

        self.setState(PLAYER_PLAY)
        self.startXine()

    def startXine(self):
        isvideo = 0
        if self._playingSourceName == "video":
            isvideo = 1
        self.xine.start_playing(self._uri,isvideo)

    def pause(self):
        if self.getState() == PLAYER_PLAY:
            self.xine.pause()
            self.setState(PLAYER_PAUSE)
        elif self.getState() == PLAYER_PAUSE:
            self.xine.play()
            self.setState(PLAYER_PLAY)

    def stop(self,widget = None, event = None):
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
        return True

    def isSupportedFormat(self,format):
        return True

    def getVideoFileInfo(self,file):
        return None

# vim: ts=4 sw=4 expandtab
