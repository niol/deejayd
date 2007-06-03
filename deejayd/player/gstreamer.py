# gstreamer.py

import time
import pygst
pygst.require('0.10')

import gobject
import gst
import gst.interfaces

from deejayd.player import UnknownPlayer,PLAYER_PLAY,PLAYER_PAUSE,PLAYER_STOP
from deejayd.ui import log

class NoSinkError: pass

class GstreamerPlayer(UnknownPlayer):

    def __init__(self,db,config):
        UnknownPlayer.__init__(self,db,config)

        # Open a Audio pipeline
        pipeline_dict = {"alsa":"alsasink", "oss":"osssink",\
            "auto":"autoaudiosink","esd":"esdsink"}
        pipeline =  self.config.get("gstreamer", "audio_output")
        try: audio_sink = gst.parse_launch(pipeline_dict[pipeline])
        except gobject.GError, err: audio_sink = None
        if audio_sink==None:
            raise NoSinkError

        # More audio-sink option
        if pipeline == "alsa":
            try: alsa_card = self.config.get("gstreamer", "alsa_card")
            except: pass
            else: audio_sink.set_property('device',alsa_card)

        self.bin = gst.element_factory_make('playbin')
        self.bin.set_property('video-sink', None)
        self.bin.set_property('audio-sink',audio_sink)

        self.bin.set_property("auto-flush-bus",True)
        bus = self.bin.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message)

    def init_video_support(self):
        import pygtk
        pygtk.require('2.0')

        # init video specific parms
        self.video_window = None
        self.deejayd_window = None
        self._fullscreen = int(self.db.get_state("fullscreen"))
        self._loadsubtitle = int(self.db.get_state("loadsubtitle"))

        # Open a Video pipeline
        pipeline_dict = {"x":"ximagesink", "xv":"xvimagesink",\
            "auto":"autovideosink"}
        pipeline =  self.config.get("gstreamer", "video_output")
        try: video_sink = gst.parse_launch(pipeline_dict[pipeline])
        except gobject.GError, err: raise NoSinkError
        else: 
            self.bin.set_property('video-sink', video_sink)

            bus = self.bin.get_bus()
            bus.enable_sync_message_emission()
            bus.connect('sync-message::element', self.on_sync_message)

            self._video_support = True

    def on_message(self, bus, message):
        if message.type == gst.MESSAGE_EOS:
            self.next()
        elif message.type == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            err = str(err).decode("utf8", 'replace')
            log.err("Gstreamer : " + err)

        return True

    def on_sync_message(self, bus, message):
        if message.structure is None:
            return
        message_name = message.structure.get_name()
        if message_name == 'prepare-xwindow-id' and self._video_support:
            imagesink = message.src
            imagesink.set_property("force-aspect-ratio","true")
            imagesink.set_xwindow_id(self.video_window.window.xid)

    def start_play(self):
        UnknownPlayer.start_play(self)

        self.set_state(PLAYER_PLAY)
        if self._playing_source_name == "video" and not self.deejayd_window:
            import gtk
            self.deejayd_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
            self.deejayd_window.set_title("deejayd")
            self.deejayd_window.connect("destroy", self.stop)
            self.video_window = gtk.DrawingArea()
            self.deejayd_window.add(self.video_window)
            self.deejayd_window.connect("map_event",self.start_gstreamer)
            self.deejayd_window.show_all()
        else: self.start_gstreamer()

    def start_gstreamer(self,widget = None, event = None):
        self.bin.set_property('uri',self._uri)
        if self._video_support: self.set_subtitle(self._loadsubtitle)

        state_ret = self.bin.set_state(gst.STATE_PLAYING)
        timeout = 4
        state = None

        while state_ret == gst.STATE_CHANGE_ASYNC and timeout > 0:
            state_ret,state,pending_state = self.bin.get_state(1 * gst.SECOND)
            timeout -= 1
        
        if state_ret != gst.STATE_CHANGE_SUCCESS: self.set_state(PLAYER_STOP)
        elif self._video_support: self.set_fullscreen(self._fullscreen)

    def pause(self):
        if self.get_state() == PLAYER_PLAY:
            self.bin.set_state(gst.STATE_PAUSED)
            self.set_state(PLAYER_PAUSE)
        elif self.get_state() == PLAYER_PAUSE:
            self.bin.set_state(gst.STATE_PLAYING)
            self.set_state(PLAYER_PLAY)

    def stop(self,widget = None, event = None):
        self.bin.set_state(gst.STATE_NULL)
        self.set_state(PLAYER_STOP)
        # Reset the queue
        self._queue.reset()

        # destroy video window if necessary
        if self._video_support and self.deejayd_window:
            self.deejayd_window.destroy()
            self.deejayd_window = None

    def set_fullscreen(self,val):
        if  self._video_support and self.deejayd_window:
            import gtk
            if val == 0:
                # Set the cursor visible
                self.deejayd_window.window.set_cursor(None)
                self.deejayd_window.unfullscreen()
            else:
                # Hide the cursor
                empty_pixmap = gtk.gdk.Pixmap(None, 1, 1, 1)
                empty_color = gtk.gdk.Color()
                empty_cursor = gtk.gdk.Cursor(empty_pixmap, empty_pixmap,
                    empty_color, empty_color, 0, 0)
                self.deejayd_window.window.set_cursor(empty_cursor)
                self.deejayd_window.fullscreen()

    def set_subtitle(self,val):
        if  self._video_support and self._source_name == "video" and val == 1:
            current_song = self._source.get_current()
            sub_uri = current_song["Subtitle"]
            if sub_uri.startswith("file://"): pass
                # FIXME : these 2 lines induce a general stream error in 
                #         gstreamer. Find out the reason
                #self.bin.set_property('suburi', subURI)
                #self.bin.set_property('subtitle-font-desc','Sans Bold 24')
        #else: self.bin.set_property('suburi', '')

    def get_volume(self):
        return int(self.bin.get_property('volume')*100)

    def set_volume(self,vol):
        v = float(vol)/100
        self.bin.set_property('volume', v)
        return True

    def get_position(self):
        if gst.STATE_NULL != self.__get_gst_state() and \
                self.bin.get_property('uri'):
            try: p = self.bin.query_position(gst.FORMAT_TIME)[0]
            except gst.QueryError: p = 0
            p //= gst.SECOND
            return p
        return 0

    def set_position(self,pos):
        if gst.STATE_NULL != self.__get_gst_state() and \
                self.bin.get_property('uri'):
            pos = max(0, int(pos))
            gst_time = pos * gst.SECOND

            event = gst.event_new_seek(
                1.0, gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH | \
                gst.SEEK_FLAG_ACCURATE, gst.SEEK_TYPE_SET, gst_time, \
                gst.SEEK_TYPE_NONE, 0)
            self.bin.send_event(event)

    def __get_gst_state(self):
        changestatus,state,_state = self.bin.get_state()
        return state

    #
    # file format info
    #
    def webradio_support(self):
        if gst.element_make_from_uri(gst.URI_SRC, "http://", ""): return True
        else:
            log.msg(\
                "gstreamer requires gst-plugins-gnomevfs to support webradio.")
            return False

    def is_supported_format(self,format):
        # MP3 file
        if format in (".mp3",".mp2"):
            return gst.registry_get_default().find_plugin("mad") is not None
        
        # OGG file
        if format in (".ogg",):
            return gst.registry_get_default().find_plugin("ogg") is not None \
               and gst.registry_get_default().find_plugin("vorbis") is not None
        
        # Video file
        if format in (".avi",".mpeg",".mpg"):
            return self._video_support and gst.registry_get_default().\
                find_plugin("ffmpeg") is not None

    def get_video_file_info(self,file):
        return DiscoverVideoFile(file)


class InfoNotFound: pass 

class DiscoverVideoFile:
    
    def __init__(self,f):
        self.__file = f.encode('utf-8')
        self.__process = False
        self.__file_info = None

    def __getitem__(self,key):
        if not self.__file_info:
            self.__getinfo()

        if key in self.__file_info: return self.__file_info[key]
        else: raise InfoNotFound

    def __getinfo(self):
        self.__process = True

        from gst.extend.discoverer import Discoverer
        self.current = Discoverer(self.__file)
        self.current.connect('discovered', self._process_end)
        # start the discover
        self.current.discover()
        self.__wait()

    def _process_end(self,discoverer,ismedia):
        # format file infos
        self.__file_info = {}
        self.__file_info["videowidth"] = self.current.videowidth 
        self.__file_info["videoheight"] = self.current.videoheight 
        self.__file_info["length"] = self.__format_time(\
            max(self.current.audiolength, self.current.videolength)) 

        self.__process = False

    def __wait(self):
        while self.__process:
            time.sleep(0.1)

    def __format_time(self,value):
        return value / gst.SECOND

# vim: ts=4 sw=4 expandtab
