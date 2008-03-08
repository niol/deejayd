# Deejayd, a media player daemon
# Copyright (C) 2007-2008 Mickael Royer <mickael.royer@gmail.com>
#                         Alexandre Rossi <alexandre.rossi@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import time
import pygst
pygst.require('0.10')

import gobject
import gst
import gst.interfaces

from ConfigParser import NoOptionError
from deejayd.player import PlayerError
from deejayd.player._base import *
from deejayd.ui import log

class GstreamerPlayer(UnknownPlayer):
    name = 'gstreamer'

    def __init__(self, db, config):
        UnknownPlayer.__init__(self, db, config)
        self.__volume = 100

        # Open a Audio pipeline
        pipeline_dict = {"alsa":"alsasink", "oss":"osssink",\
            "auto":"autoaudiosink","esd":"esdsink"}
        pipeline =  self.config.get("gstreamer", "audio_output")
        try: audio_sink = gst.parse_launch(pipeline_dict[pipeline])
        except gobject.GError, err: audio_sink = None
        if audio_sink==None:
            raise PlayerError(_("No audio sink found for Gstreamer"))

        # More audio-sink option
        if pipeline == "alsa":
            try: alsa_card = self.config.get("gstreamer", "alsa_card")
            except NoOptionError: pass
            else: audio_sink.set_property('device',alsa_card)

        self.bin = gst.element_factory_make('playbin')
        self.bin.set_property('video-sink', None)
        self.bin.set_property('audio-sink',audio_sink)

        self.bin.set_property("auto-flush-bus",True)
        bus = self.bin.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message)

    def init_video_support(self):
        UnknownPlayer.init_video_support(self)

        import pygtk
        pygtk.require('2.0')

        self.video_window = None
        self.deejayd_window = None

        # Open a Video pipeline
        pipeline_dict = {"x":"ximagesink", "xv":"xvimagesink",\
            "auto":"autovideosink"}
        pipeline =  self.config.get("gstreamer", "video_output")
        try: video_sink = gst.parse_launch(pipeline_dict[pipeline])
        except gobject.GError, err:
            self._video_support = False
            raise PlayerError(_("No video sink found for Gstreamer"))
        else:
            self.bin.set_property('video-sink', video_sink)

            bus = self.bin.get_bus()
            bus.enable_sync_message_emission()
            bus.connect('sync-message::element', self.on_sync_message)

    def on_message(self, bus, message):
        if message.type == gst.MESSAGE_EOS:
            self.next()
        elif message.type == gst.MESSAGE_TAG:
            self._update_metadata(message.parse_tag())
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
        if not self._media_file: return

        if self._media_file["type"] == "video" and not self.deejayd_window:
            import gtk
            self.deejayd_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
            self.deejayd_window.set_default_size(640,400)
            self.deejayd_window.set_title("deejayd")
            self.deejayd_window.connect("destroy", self.stop)

            self.video_window = gtk.DrawingArea()
            self.deejayd_window.add(self.video_window)
            self.deejayd_window.connect("map_event",self.start_gstreamer)
            if self._fullscreen:
                # Hide the cursor
                empty_pixmap = gtk.gdk.Pixmap(None, 1, 1, 1)
                empty_color = gtk.gdk.Color()
                empty_cursor = gtk.gdk.Cursor(empty_pixmap, empty_pixmap,
                    empty_color, empty_color, 0, 0)
                self.deejayd_window.window.set_cursor(empty_cursor)
                self.deejayd_window.fullscreen()
            self.deejayd_window.show_all()
        else: self.start_gstreamer()

    def start_gstreamer(self,widget = None, event = None):
        self.bin.set_property('uri',self._media_file["uri"])
        # load external subtitle if available
        self.bin.set_property("suburi",'')
        if "external_subtitle" in self._media_file and \
                self._media_file["external_subtitle"].startswith("file://"):
            self.bin.set_property("suburi",\
                self._media_file["external_subtitle"])
            self.bin.set_property("subtitle-font-desc", "Sans Normal 24")
            #self._media_file["subtitle"] = [{"lang": "none", "ix": -1},\
            #                                {"lang": "external", "ix":0}]

        state_ret = self.bin.set_state(gst.STATE_PLAYING)
        timeout = 4
        state = None

        while state_ret == gst.STATE_CHANGE_ASYNC and timeout > 0:
            state_ret,state,pending_state = self.bin.get_state(1 * gst.SECOND)
            timeout -= 1

        if state_ret != gst.STATE_CHANGE_SUCCESS:
            msg = _("Unable to play file %s") % self._media_file["uri"]
            raise PlayerError(msg)
        elif self._media_file["type"] == "video":
            if "audio" in self._media_file:
                self._media_file["audio_idx"] = \
                                self.bin.get_property("current-audio")
            if "subtitle" in self._media_file:
                self._media_file["subtitle_idx"] = \
                                self.bin.get_property("current-text")

    def pause(self):
        if self.get_state() == PLAYER_PLAY:
            self.bin.set_state(gst.STATE_PAUSED)
        elif self.get_state() == PLAYER_PAUSE:
            self.bin.set_state(gst.STATE_PLAYING)

    def stop(self,widget = None, event = None):
        self._media_file = None
        self.bin.set_state(gst.STATE_NULL)
        # FIXME : try to remove this one day ...
        self._source.queue_reset()

        # destroy video window if necessary
        if self._video_support and self.deejayd_window:
            self.deejayd_window.destroy()
            self.deejayd_window = None

        self.dispatch_signame('player.status')

    def _change_file(self,new_file):
        sig = self.get_state() == PLAYER_STOP and True or False
        self.stop()
        self._media_file = new_file
        self.start_play()

        # replaygain reset
        self.set_volume(self.__volume)

        if sig:
            self.dispatch_signame('player.status')
        self.dispatch_signame('player.current')

    def get_volume(self):
        return self.__volume

    def set_volume(self,vol):
        self.__volume = min(100, int(vol))
        v = float(self.__volume)/100
        # replaygain support
        if self._replaygain and self._media_file is not None:
            try: scale = self._media_file.replay_gain()
            except AttributeError: pass # replaygain not supported
            else:
                v = max(0.0, min(4.0, v * scale))
                v = min(100, int(v * 100))
        self.bin.set_property('volume', v)
        self.dispatch_signame('player.status')

    def get_position(self):
        if gst.STATE_NULL != self.__get_gst_state() and \
                self.bin.get_property('uri'):
            try: p = self.bin.query_position(gst.FORMAT_TIME)[0]
            except gst.QueryError: return 0
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
            self.dispatch_signame('player.status')

    def _player_get_alang(self):
        return self.bin.get_property("current-audio")

    def _player_set_alang(self,lang_idx):
        self.bin.set_property("current-audio",lang_idx)

    def _player_get_slang(self):
        return self.bin.get_property("current-text")

    def _player_set_slang(self,lang_idx):
        self.bin.set_property("current-text",lang_idx)

    def _update_metadata(self, tags):
        if not self._media_file or self._media_file["type"] != "webradio":
            return

        for k in tags.keys():
            value = str(tags[k]).strip()
            if not value: continue
            if k in ("emphasis", "mode", "layer"):
                continue
            elif isinstance(value, basestring):
                if k in ("title", "album", "artist"):
                    name = "song-" + k
                    if name not in self._media_file.keys() or\
                                   self._media_file[name] != value:
                        self._media_file[name] = value

    def get_state(self):
        gst_state = self.__get_gst_state()
        if gst_state == gst.STATE_PLAYING:
            return PLAYER_PLAY
        elif gst_state == gst.STATE_PAUSED:
            return PLAYER_PAUSE
        else:
            return PLAYER_STOP

    def __get_gst_state(self):
        changestatus,state,_state = self.bin.get_state()
        return state

    def is_supported_uri(self,uri_type):
        if uri_type == "dvd" and not self._is_lsdvd_exists():
            # test lsdvd  installation
            return False
        return gst.element_make_from_uri(gst.URI_SRC,uri_type+"://", '') \
                    is not None

    def is_supported_format(self,format):
        formats = {
            ".mp3": ("mad",),
            ".mp2": ("mad",),
            ".ogg": ("ogg", "vorbis"),
            ".mp4": ("faad",),
            ".flac": ("flac",),
            ".avi": ("ffmpeg",),
            ".mpeg": ("ffmpeg",),
            ".mpg": ("ffmpeg",),
            }

        if format in formats.keys():
            for plugin in formats[format]:
                if gst.registry_get_default().find_plugin(plugin) == None:
                    return False
            return True

        return False

    def get_video_file_info(self,file):
        return DiscoverVideoFile(file)

    def get_dvd_info(self):
        dvd_info = self._get_dvd_info()
        ix = 0
        for track in dvd_info["track"]:
            # FIXME find audio channels
            audio_channels = [{"lang":"none","ix":-1},{"lang":"auto","ix":0}]
            dvd_info['track'][ix]["audio"] = []
            # FIXME find subtitles channels
            sub_channels = [{"lang":"none","ix":-1},{"lang":"auto","ix":0}]
            dvd_info['track'][ix]["subp"] = []

            ix += 1
        return dvd_info


class DiscoverVideoFile:

    def __init__(self,f):
        self.__file = f.encode('utf-8')
        self.__process = False
        self.__file_info = None

    def __getitem__(self,key):
        if not self.__file_info:
            self.__getinfo()

        if key in self.__file_info: return self.__file_info[key]
        else: raise PlayerError

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
