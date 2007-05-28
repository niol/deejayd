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

def wait_for_attach(func):
    def wait_for_attach_wrapper(self, *args):
        if self.attached:
            func(self, *args)
        else:
            self.attach_queue.append((func, args))
    return wait_for_attach_wrapper


class XinePlayer(unknownPlayer):

    def __init__(self,db,config):
        unknownPlayer.__init__(self,db,config)
        self.xine = xine.Xine("alsa")
        self.xine.set_eos_callback(self.eos)

    def eos(self):
        song = self._queue.next(self._random,self._repeat) or\
                self._source.next(self._random,self._repeat)

        if song:
            unknownPlayer.startPlay(self)
            self.setURI(song["uri"])
            isvideo = 0
            if self._playingSourceName == "video":
                isvideo = 1
            self.xine.next(self._uri,isvideo)
        else: self.stop()

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
        pass

    def setSubtitle(self,val):
        pass

    def getVolume(self):
        try: vol = self.xine.get_volume()
        except xine.NotPlayingError: return 0
        else: return vol

    def setVolume(self,vol):
        try: self.xine.set_volume(vol)
        except xine.NotPlayingError: pass
        return True

    def getPosition(self):
        #pos, length = self.xine.getPositionAndLength()
        #return pos / 1000
        return 0

    def setPosition(self,pos):
        self.xine.seek(int(pos * 1000))

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
