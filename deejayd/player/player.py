
import sys
import time
import pygst
pygst.require('0.10')

import gobject
import gst
import gst.interfaces

from twisted.python import log
from deejayd.ui.config import DeejaydConfig

PLAYER_PLAY = "play"
PLAYER_PAUSE = "pause"
PLAYER_STOP = "stop"

class NoSinkError: pass

class deejaydPlayer:

    def __init__(self,db):
        self.db = db
        # Initialise var
        self.__state = PLAYER_STOP
        self.__queue = None
        self.__source = None
        self.__sourceName = None
        self.__playingSourceName = None
        self.__playingSource = None
        self.__random = 0
        self.__repeat = 0

        # Open a pipeline
        pipeline = DeejaydConfig().get("player", "output")
        if pipeline == "gconf": pipeline = "gconfaudiosink"
        else: pipeline = pipeline + "sink"

        try: audio_sink = gst.parse_launch(pipeline)
        except gobject.GError, err:
            if pipeline != "autoaudiosink":
                try: audio_sink = gst.parse_launch("autoaudiosink")
                except gobject.GError: audio_sink = None
                else: pipeline = "autoaudiosink"
            else: audio_sink = None

        if audio_sink==None:
            raise NoSinkError

        self.bin = gst.element_factory_make('playbin')
        self.bin.set_property('video-sink', None)
        self.bin.set_property('audio-sink',audio_sink)

        self.bin.set_property("auto-flush-bus",True)
        bus = self.bin.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message)

    def on_message(self, bus, message):
        if message.type == gst.MESSAGE_EOS:
            self.next()
        elif message.type == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            err = str(err).decode("utf8", 'replace')
            log.err(err)

        return True

    def loadState(self):
        # Restore volume
        vol = float(self.db.getState("volume"))
        self.setVolume(vol)

        # Restore current song
        curPos = int(self.db.getState("currentPos"))
        self.__source.goTo(curPos,"Pos")

        # Random and Repeat
        self.__random = int(self.db.getState("random"))
        self.__repeat = int(self.db.getState("repeat"))


    def setSource(self,source,name):
        self.__source = source
        self.__sourceName = name

    def setQueue(self,queue):
        self.__queue = queue

    def getPlayingSourceName(self):
        return self.__playingSourceName or self.__sourceName

    def __startPlay(self):
        if self.__queue.getCurrent():
            self.__playingSourceName = "queue"
            self.__playingSource = self.__queue
        else:
            self.__playingSourceName = self.__sourceName
            self.__playingSource= self.__source

        state_ret = self.bin.set_state(gst.STATE_PLAYING)
        self.__state = PLAYER_PLAY
        timeout = 4
        state = None

        while state_ret == gst.STATE_CHANGE_ASYNC and timeout > 0:
            state_ret,state,pending_state = self.bin.get_state(1 * gst.SECOND)
            timeout -= 1
        
        if state_ret != gst.STATE_CHANGE_SUCCESS:
            self.__state = PLAYER_STOP

    def play(self):
        if self.__state == PLAYER_STOP:
            curSong = self.__queue.goTo(0,"Pos") or self.__source.getCurrent()
            if curSong: self.bin.set_property('uri',curSong["uri"])
            else: return
        self.__startPlay()


    def pause(self):
        if self.__state == PLAYER_PLAY:
            self.bin.set_state(gst.STATE_PAUSED)
            self.__state = PLAYER_PAUSE
        elif self.__state == PLAYER_PAUSE:
            self.play(setURI = False)

    def stop(self):
        self.bin.set_state(gst.STATE_NULL)
        self.__state = PLAYER_STOP
        # Reset the queue
        self.__queue.reset()

    def reset(self,sourceName):
        if sourceName == self.__playingSourceName:
            self.stop()
            self.bin.set_property('uri',"")

    def next(self):
        self.stop()
        song = self.__queue.next(self.__random,self.__repeat) or\
                self.__source.next(self.__random,self.__repeat)

        if song:
            self.bin.set_property('uri',song["uri"])
            self.__startPlay()

    def previous(self):
        self.stop()
        song = self.__source.previous(self.__random,self.__repeat)
        if song:
            self.bin.set_property('uri',song["uri"])
            self.__startPlay()

    def goTo(self,nb,type,queue = False):
        self.stop()
        s = queue and self.__queue or self.__source
        song = s.goTo(nb,type)
        if song:
            self.bin.set_property('uri',song["uri"])
            self.__startPlay()

    def random(self,val):
        self.__random = val

    def repeat(self,val):
        self.__repeat = val

    def getVolume(self):
        return self.bin.get_property('volume')

    def setVolume(self,v):
        self.bin.set_property('volume', v)
        return True

    def getPosition(self):
        if gst.STATE_NULL != self.__getGstState() and \
                self.bin.get_property('uri'):
            try: p = self.bin.query_position(gst.FORMAT_TIME)[0]
            except gst.QueryError: p = 0
            p //= gst.SECOND
            return p
        return 0

    def setPosition(self,pos):
        if gst.STATE_NULL != self.__getGstState() and \
                self.bin.get_property('uri'):
            pos = max(0, int(pos))
            gst_time = pos * gst.SECOND

            event = gst.event_new_seek(
                1.0, gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH | \
                gst.SEEK_FLAG_ACCURATE, gst.SEEK_TYPE_SET, gst_time, \
                gst.SEEK_TYPE_NONE, 0)
            self.bin.send_event(event)

    def getStatus(self):
        status = [("random",self.__random),("repeat",self.__repeat),\
            ("state",self.__state),("volume",int(self.getVolume()*100)),\
            ("mode",self.__sourceName)]

        source = self.__playingSource or self.__source
        curSong = source.getCurrent()
        if curSong:
            status.extend([("song",curSong["Pos"]),("songid",curSong["Id"])])
        if self.__state != PLAYER_STOP:
            if "Time" not in curSong.keys() or curSong["Time"] == 0:
                curSong["Time"] = self.getPosition()
            status.extend([ ("time","%d:%d" % (self.getPosition(),\
                curSong["Time"])) ])

        return status

    def isPlay(self):
        return self.__state != PLAYER_STOP

    def close(self):
        song = self.__source.getCurrent()
        if song: curPos = song["Pos"]
        else: curPos = 0

        states = [(str(self.getVolume()),"volume"),(str(self.__repeat),\
            "repeat"),(str(self.__random),"random"),\
            (self.__sourceName,"source"),(str(curPos),"currentPos")]
        self.db.setState(states)

    def __getGstState(self):
        changestatus,state,_state = self.bin.get_state()
        return state


# vim: ts=4 sw=4 expandtab
