
import sys
import time
import pygst
pygst.require('0.10')

import gobject
import gst
import gst.interfaces

from deejayd.ui.config import DeejaydConfig

PLAYER_PLAY = "play"
PLAYER_PAUSE = "pause"
PLAYER_STOP = "stop"

class NoSinkError: pass

class deejaydPlayer:

    def __init__(self,db):
        self.db = db
        # Initialise var
        self.__videoSupport = False
        self.__state = PLAYER_STOP
        self.__queue = None
        self.__source = None
        self.__sourceName = None
        self.__playingSourceName = None
        self.__playingSource = None
        self.__random = 0
        self.__repeat = 0

        self.config = DeejaydConfig()

        # Open a Audio pipeline
        pipeline =  self.config.get("player", "audio_output")
        try: audio_sink = gst.parse_launch(pipeline)
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
        self.__fullscreen = False
        # Open a Video pipeline
        pipeline =  self.config.get("player", "video_output")
        try: video_sink = gst.parse_launch(pipeline)
        except gobject.GError, err: raise NoSinkError
        else: 
            self.bin.set_property('video-sink', video_sink)

            bus = self.bin.get_bus()
            bus.enable_sync_message_emission()
            bus.connect('sync-message::element', self.on_sync_message)

            self.__videoSupport = True


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
        if message_name == 'prepare-xwindow-id' and self.__videoSupport:
            imagesink = message.src
            imagesink.set_property('force-aspect-ratio', True)
            imagesink.set_xwindow_id(self.videoWindow.window.xid)

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

        if self.__playingSourceName == "video" and not self.deejaydWindow:
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
            self.play()

    def stop(self,widget = None, event = None):
        self.bin.set_state(gst.STATE_NULL)
        self.__state = PLAYER_STOP
        # Reset the queue
        self.__queue.reset()

        # destroy video window if necessary
        if self.__videoSupport and self.deejaydWindow:
            self.deejaydWindow.destroy()
            self.deejaydWindow = None
            self.__fullscreen = False

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

    def fullscreen(self,val):
        if  self.__videoSupport and self.deejaydWindow:
            import gtk
            if val == 0:
                # Set the cursor visible
                self.deejaydWindow.window.set_cursor(None)

                self.deejaydWindow.unfullscreen()
                self.__fullscreen = False
            else:
                # Hide the cursor
                emptyPixmap = gtk.gdk.Pixmap(None, 1, 1, 1)
                emptyColor = gtk.gdk.Color()
                emptyCursor = gtk.gdk.Cursor(emptyPixmap, emptyPixmap,
                    emptyColor, emptyColor, 0, 0)
                self.deejaydWindow.window.set_cursor(emptyCursor)

                self.deejaydWindow.fullscreen()
                self.__fullscreen = True

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
                    
        # Specific video status
        if self.__videoSupport:
            status.extend([("fullscreen",self.__fullscreen)])

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
