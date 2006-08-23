
import gobject
import gst
import sys

class Player(gobject.GObject):

    def __init__(self):
        gobject.GObject.__init__(self)

        # Initialise var
        self.paused = True
        self.__volume = 0

        # Open a pipeline
        try: audio_sink = gst.parse_launch("gconfaudiosink")
        except gobject.GError, err:
            try: audio_sink = gst.parse_launch("autoaudiosink")
            except gobject.GError: audio_sink = None

        if audio_sink==None:
            sys.exit(1)

        self.bin = gst.element_factory_make('playbin')
        self.bin.set_property('audio-sink',audio_sink)
        self.bin.set_property("auto-flush-bus",True)

        self.bin.set_state(gst.STATE_NULL)

    def set_song(self,uri):
        self.bin.set_state(gst.STATE_NULL)
        self.bin.set_property('uri',uri)

        return True

    def play(self):
        if self.bin.get_property('uri'):
            state_ret = self.bin.set_state(gst.STATE_PLAYING)
            self.paused = False
            timeout = 4
            state = None

            while state_ret == gst.STATE_CHANGE_ASYNC and not self.paused and timeout > 0:
                state_ret,state,pending_state = self.bin.get_state(1 * gst.SECOND)
                timeout -= 1
        
            if state_ret != gst.STATE_CHANGE_SUCCESS:
                self.paused = True

    def pause(self):
        if not self.paused:
            self.bin.set_state(gst.STATE_PAUSED)
            self.paused = True
        else:
            self.play()

    def stop(self):
        self.bin.set_state(gst.STATE_NULL)
        self.paused = True

    def get_volume(self):
        return self.__volume

    def set_volume(self,v):
        self.__volume = v
        self.bin.set_property('volume', v)

    def get_state(self):
        changestatus,state,_state = self.bin.get_state()
        return state

    def get_position(self):
        if gst.STATE_NULL != self.get_state() and self.bin.get_property('uri'):
            try: p = self.bin.query_position(gst.FORMAT_TIME)[0]
            except gst.QueryError: p = 0
            p //= gst.MSECOND
            return p
        return 0

    def set_position(self,pos):
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
                

# vim: ts=4 sw=4 expandtab
