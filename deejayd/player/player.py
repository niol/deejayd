
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

    def __init__(self):
        # Initialise var
        self.__state = PLAYER_STOP
        self.__source = None
        self.__sourceName = ""
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
            self.error(err)

        return True

    def setSource(self,source,name):
        self.__source = source
        self.__sourceName = name

    def play(self):
        if not self.bin.get_property('uri'):
            try: 
                curSong = self.__source.getCurrent()
                self.bin.set_property('uri',curSong["uri"])
            except: return

        state_ret = self.bin.set_state(gst.STATE_PLAYING)
        self.__state = PLAYER_PLAY
        timeout = 4
        state = None

        while state_ret == gst.STATE_CHANGE_ASYNC and timeout > 0:
            state_ret,state,pending_state = self.bin.get_state(1 * gst.SECOND)
            timeout -= 1
        
        if state_ret != gst.STATE_CHANGE_SUCCESS:
            self.__state = PLAYER_STOP

    def pause(self):
        if self.__state == PLAYER_PLAY:
            self.bin.set_state(gst.STATE_PAUSED)
            self.__state = PLAYER_PAUSE
        else:
            self.play()

    def stop(self):
        self.bin.set_state(gst.STATE_NULL)
        self.__state = PLAYER_STOP

    def reset(self):
        self.stop()
        self.bin.set_property('uri',"")

    def next(self):
        self.stop()
        song = self.__source.next(self.__random,self.__repeat)
        try: 
            self.bin.set_property('uri',song["uri"])
            self.play()
        except: return

    def previous(self):
        self.stop()
        song = self.__source.previous(self.__random,self.__repeat)
        try: 
            self.bin.set_property('uri',song["uri"])
            self.play()
        except: return

    def goTo(self,nb,type):
        self.stop()
        song = self.__source.goTo(nb,type)
        try: 
            self.bin.set_property('uri',song["uri"])
            self.play()
        except: return

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
        if gst.STATE_NULL != self.__getGstState() and self.bin.get_property('uri'):
            try: p = self.bin.query_position(gst.FORMAT_TIME)[0]
            except gst.QueryError: p = 0
            p //= gst.SECOND
            return p
        return 0

    def setPosition(self,pos):
        if gst.STATE_NULL != self.__getGstState() and self.bin.get_property('uri'):
            pos = max(0, int(pos))
            gst_time = pos * gst.SECOND

            event = gst.event_new_seek(
                1.0, gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_ACCURATE,
                gst.SEEK_TYPE_SET, gst_time, gst.SEEK_TYPE_NONE, 0)
            self.bin.send_event(event)

    def getStatus(self):
        status = [("random",self.__random),("repeat",self.__repeat),("state",self.__state),\
            ("volume",int(self.getVolume()*100)),("mode",self.__sourceName)]
        curSong = self.__source.getCurrent()
        if curSong:
            status.extend([("song",curSong["Pos"]),("songid",curSong["Id"])])
        if self.__state != PLAYER_STOP:
            if "Time" not in curSong.keys():
                curSong["Time"] = 0
            status.extend([ ("time","%d:%d" % (self.getPosition(),curSong["Time"])) ])

        return status

    def close(self):
        pass

    def error(self,error):
        log.msg("ERROR : " + error)

    def __getGstState(self):
        changestatus,state,_state = self.bin.get_state()
        return state

# vim: ts=4 sw=4 expandtab
