
import sys
import time
import pygst
pygst.require('0.10')

import gobject
import gst
import gst.interfaces

from twisted.internet import threads

PLAYER_PLAY = 0
PLAYER_PAUSE = 1
PLAYER_STOP = 2

class Player:

    def __init__(self):
        # Initialise var
        self.__state = PLAYER_STOP
        self.on_eos = False
        self.defd = None

        # Open a pipeline
        try: audio_sink = gst.parse_launch("gconfaudiosink")
        except gobject.GError, err:
            try: audio_sink = gst.parse_launch("autoaudiosink")
            except gobject.GError: audio_sink = None

        if audio_sink==None:
            sys.exit(1)

        self.bin = gst.element_factory_make('playbin')
        self.bin.set_property('video-sink', None)
        self.bin.set_property('audio-sink',audio_sink)

        """self.bin.set_property("auto-flush-bus",True)
        bus = self.bin.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message)

    def on_message(self, bus, message):
        print "message"
        if message.type == gst.MESSAGE_EOS:
            if self.on_eos:
                self.on_eos()
        elif message.type == gst.MESSAGE_ERROR:
            pass

        return True"""

    def setURI(self,uri):
        self.stop()
        self.bin.set_property('uri',uri)

        return True

    def play(self):
        if self.bin.get_property('uri'):
            state_ret = self.bin.set_state(gst.STATE_PLAYING)
            self.__state = PLAYER_PLAY
            timeout = 4
            state = None

            while state_ret == gst.STATE_CHANGE_ASYNC and timeout > 0:
                state_ret,state,pending_state = self.bin.get_state(1 * gst.SECOND)
                timeout -= 1
        
            if state_ret != gst.STATE_CHANGE_SUCCESS:
                self.__state = PLAYER_STOP
            else:
                # FIXME : Very bad
                if self.on_eos != None: 
                    self.defd = threads.deferToThread(self.__watchGstState)
                    self.defd.addCallback(self.on_eos)
     
    def __watchGstState(self):
        # Return when the song finishes
        position = None
        while position != self.getPosition():
            position = self.getPosition()
            time.sleep(0.1)
        return True

    def pause(self):
        if self.__state == PLAYER_PLAY:
            self.defd.pause()
            self.bin.set_state(gst.STATE_PAUSED)
            self.__state = PLAYER_PAUSE
        else:
            self.play()

    def stop(self):
        if self.defd:
            self.defd.pause()
        self.bin.set_state(gst.STATE_NULL)
        self.__state = PLAYER_STOP

    def getState(self):
        return self.__state

    def getVolume(self):
        return self.bin.get_property('volume')

    def setVolume(self,v):
        self.bin.set_property('volume', v)

    def getPosition(self):
        if gst.STATE_NULL != self.__getGstState() and self.bin.get_property('uri'):
            try: p = self.bin.query_position(gst.FORMAT_TIME)[0]
            except gst.QueryError: p = 0
            p //= gst.MSECOND
            return p
        return 0

    def setPosition(self,pos):
        if self.bin.get_property('uri'):
            pos = max(0, int(pos))
            gst_time = pos * gst.MSECOND

            event = gst.event_new_seek(
                1.0, gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_ACCURATE,
                gst.SEEK_TYPE_SET, gst_time, gst.SEEK_TYPE_NONE, 0)
            res = self.bin.send_event(event)
            if res:
                self.bin.set_new_stream_time(0L)
            else:
                pass

    def __getGstState(self):
        changestatus,state,_state = self.bin.get_state()
        return state


global djPlayer
djPlayer = Player()

# vim: ts=4 sw=4 expandtab
