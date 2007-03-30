# gstreamer.py

import sys
import time
import pygst
pygst.require('0.10')

import gobject
import gst
import gst.interfaces

from deejayd.player.unknown import unknownPlayer

PLAYER_PLAY = "play"
PLAYER_PAUSE = "pause"
PLAYER_STOP = "stop"

class NoSinkError: pass

class Gstreamer(unknownPlayer):

    def __init__(self,db,config):
        unknownPlayer.__init__(self,db,config)

        # Open a Audio pipeline
        pipeline_dict = {"alsa":"alsasink", "oss":"osssink",\
            "auto":"autoaudiosink","esd":"esdsink"}
        pipeline =  self.config.get("player", "audio_output")
        try: audio_sink = gst.parse_launch(pipeline_dict[pipeline])
        except gobject.GError, err: audio_sink = None
        if audio_sink==None:
            raise NoSinkError

        self.bin = gst.element_factory_make('playbin')
        self.bin.set_property('video-sink', None)
        self.bin.set_property('audio-sink',audio_sink)

        self.bin.set_property("auto-flush-bus",True)
        bus = self.bin.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message)

    def initVideoSupport(self):
        import pygtk
        pygtk.require('2.0')

        # init video specific parms
        self.videoWindow = None
        self.deejaydWindow = None
        self._fullscreen = False
        # Open a Video pipeline
        pipeline_dict = {"x":"ximagesink", "xv":"xvimagesink",\
            "auto":"autovideosink"}
        pipeline =  self.config.get("player", "video_output")
        try: video_sink = gst.parse_launch(pipeline_dict[pipeline])
        except gobject.GError, err: raise NoSinkError
        else: 
            self.bin.set_property('video-sink', video_sink)

            bus = self.bin.get_bus()
            bus.enable_sync_message_emission()
            bus.connect('sync-message::element', self.on_sync_message)

            self._videoSupport = True

    def on_message(self, bus, message):
        if message.type == gst.MESSAGE_EOS:
            self.next()
        elif message.type == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            err = str(err).decode("utf8", 'replace')
            log.err(err)

        return True

    def on_sync_message(self, bus, message):
        if message.structure is None:
            return
        message_name = message.structure.get_name()
        if message_name == 'prepare-xwindow-id' and self._videoSupport:
            imagesink = message.src
            imagesink.set_property('force-aspect-ratio', True)
            imagesink.set_xwindow_id(self.videoWindow.window.xid)

    def setURI(self,uri):
        self.bin.set_property('uri',uri)

    def startPlay(self):
        unknownPlayer.startPlay(self)

        if self._playingSourceName == "video" and not self.deejaydWindow:
            import gtk
            self.deejaydWindow = gtk.Window(gtk.WINDOW_TOPLEVEL)
            self.deejaydWindow.set_title("deejayd")
            self.deejaydWindow.connect("destroy", self.stop)
            self.videoWindow = gtk.DrawingArea()
            self.deejaydWindow.add(self.videoWindow)
            self.deejaydWindow.connect("map_event",self.startGst)
            self.deejaydWindow.show_all()
            self.deejaydWindow.maximize()
        else: self.startGst()

    def startGst(self,widget = None, event = None):
        state_ret = self.bin.set_state(gst.STATE_PLAYING)
        self._state = PLAYER_PLAY
        timeout = 4
        state = None

        while state_ret == gst.STATE_CHANGE_ASYNC and timeout > 0:
            state_ret,state,pending_state = self.bin.get_state(1 * gst.SECOND)
            timeout -= 1
        
        if state_ret != gst.STATE_CHANGE_SUCCESS:
            self._state = PLAYER_STOP

    def pause(self):
        if self._state == PLAYER_PLAY:
            self.bin.set_state(gst.STATE_PAUSED)
            self._state = PLAYER_PAUSE
        elif self._state == PLAYER_PAUSE:
            self.play()

    def stop(self,widget = None, event = None):
        self.bin.set_state(gst.STATE_NULL)
        self._state = PLAYER_STOP
        # Reset the queue
        self._queue.reset()

        # destroy video window if necessary
        if self._videoSupport and self.deejaydWindow:
            self.deejaydWindow.destroy()
            self.deejaydWindow = None
            self._fullscreen = False

    def fullscreen(self,val):
        if  self._videoSupport and self.deejaydWindow:
            import gtk
            if val == 0:
                # Set the cursor visible
                self.deejaydWindow.window.set_cursor(None)

                self.deejaydWindow.unfullscreen()
                self._fullscreen = False
            else:
                # Hide the cursor
                emptyPixmap = gtk.gdk.Pixmap(None, 1, 1, 1)
                emptyColor = gtk.gdk.Color()
                emptyCursor = gtk.gdk.Cursor(emptyPixmap, emptyPixmap,
                    emptyColor, emptyColor, 0, 0)
                self.deejaydWindow.window.set_cursor(emptyCursor)

                self.deejaydWindow.fullscreen()
                self._fullscreen = True

    def getVolume(self):
        return int(self.bin.get_property('volume')*100)

    def setVolume(self,vol):
        v = float(vol)/100
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

    def __getGstState(self):
        changestatus,state,_state = self.bin.get_state()
        return state

# vim: ts=4 sw=4 expandtab
