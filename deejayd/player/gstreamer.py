# Deejayd, a media player daemon
# Copyright (C) 2007-2009 Mickael Royer <mickael.royer@gmail.com>
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

import os
from twisted.internet import reactor
import pygst
pygst.require('0.10')

import gobject
import gst


from deejayd.jsonrpc.interfaces import jsonrpc_module, PlayerModule
from deejayd.player import PlayerError
from deejayd.player._base import *
from deejayd.ui import log
from pytyx11 import x11

SUB_EXTERNAL = 0

@jsonrpc_module(PlayerModule)
class GstreamerPlayer(_BasePlayer):
    NAME = 'gstreamer'
    supported_options = ("audio_lang","sub_lang","av_offset",)

    def __init__(self, db, plugin_manager, config):
        if gst.version() < (0, 10, 24):
            # we need gstreamer version >= 0.10.24 to have playbin2 support
            raise PlayerError(_("Gstreamer >= 0.10.24 is required"))

        super(GstreamerPlayer, self).__init__(db, plugin_manager, config)
        self.__gst_options = {
                "audio_p": self.config.get("gstreamer", "audio_output"),
                "video_p": self.config.get("gstreamer", "video_output"),
            }

        self.__new_file = None
        self.__in_gapless_transition = False
        # gstreamer var
        self.bin = None
        self.__bus_id = None
        self.__atf_id = None
        self.__osd = None
        self.__bus_video_id = None
        self.__display = None
        self.__window = None

    def __init_pipeline(self):
        if self.bin is not None: return

        self.bin = gst.element_factory_make('playbin2')
        self.bin.set_property("auto-flush-bus",True)

        # Open a Audio sink
        audio_sink_bin = gst.Bin()
        audiofilter = gst.element_factory_make('capsfilter')
        audioconvert = gst.element_factory_make('audioconvert')
        try:
            audio_sink = gst.parse_launch(self.__gst_options["audio_p"])
            ret = audio_sink.set_state(gst.STATE_READY)
            if ret == gst.STATE_CHANGE_FAILURE:
                raise PlayerError
        except (PlayerError, gobject.GError), err:
            raise PlayerError(_("No audio sink found for Gstreamer : %s") \
                    % str(err).decode("utf8", 'replace'))
        finally:
            audio_sink.set_state(gst.STATE_NULL)
        audio_sink_bin.add_many(audiofilter, audioconvert, audio_sink)
        audiofilter.link(audioconvert)
        audioconvert.link(audio_sink)
        audio_sink_bin.add_pad(gst.GhostPad('sink',
                               audiofilter.get_static_pad('sink')))

        audio_sink_caps = audio_sink.get_static_pad('sink').get_caps()
        wanted_channels = self.get_num_audio_channels()
        if wanted_channels != -1:
            wanted_caps = gst.Caps()
            for cap in audio_sink_caps:
                try:
                    channels = cap['channels']
                except KeyError:
                    pass
                else:
                    wanted_cap = cap.copy()
                    wanted_cap['channels'] = wanted_channels
                    wanted_caps.append_structure(wanted_cap)
            audiofilter.set_property('caps', wanted_caps)

        self.bin.set_property('audio-sink', audio_sink_bin)

        # connect to bus messages
        bus = self.bin.get_bus()
        bus.add_signal_watch()
        self.__bus_id = bus.connect('message', self.__message)
        self.__atf_id = self.bin.connect('about-to-finish',
                                         self.__about_to_finish)

        # Open a Video pipeline if video support enabled
        # [<-> Ghospad -> textoverlay (for OSD support) -> video sink]
        if self._current_is_video():
            try: video_sink = gst.parse_launch(self.__gst_options["video_p"])
            except gobject.GError, err:
                self.__destroy_pipeline()
                raise PlayerError(_("No video sink found for Gstreamer : %s") \
                        % str(err).decode("utf8", 'replace'))

            def open_display(d):
                try: self.__display = x11.X11Display(id=d)
                except x11.X11Error:
                    raise PlayerError(_("Unable to open video display"))

            if self.__gst_options["video_p"] != "fakesink":
                try: open_display(self._video_options["display"])
                except PlayerError, ex: # try to get display with env var
                    try: open_display(os.environ["DISPLAY"])
                    except (PlayerError,KeyError):
                        self.__destroy_pipeline()
                        raise ex

                bus.enable_sync_message_emission()
                self.__bus_video_id = bus.connect('sync-message::element',\
                                                  self.__sync_message)

            bufbin = gst.Bin()
            self.__osd = gst.element_factory_make('textoverlay')
            self.__osd.set_property("silent", True)
            self.__osd.set_property("halignment", 0) # left
            self.__osd.set_property("valignment", 2) # top
            bin_elts = [self.__osd, video_sink]
            map(bufbin.add, bin_elts)
            try:
                gst.element_link_many(*bin_elts)
            except gst.LinkError, e:
                err = str(e).decode("utf8", 'replace')
                self.__destroy_pipeline()
                raise PlayerError(_("Could not link GStreamer pipeline: '%s'")\
                                   % err)

            # Test to ensure output pipeline can preroll
            bufbin.set_state(gst.STATE_READY)
            result, state, pending = bufbin.get_state(timeout=gst.SECOND/2)
            if result == gst.STATE_CHANGE_FAILURE:
                bufbin.set_state(gst.STATE_NULL)
                self.__destroy_pipeline()
                raise PlayerError(_("Unable to create video pipeline"))
            # create ghostpad
            gpad = gst.GhostPad('sink', self.__osd.get_pad('video_sink'))
            bufbin.add_pad(gpad)
            vsink = bufbin
        else:
            vsink = gst.element_factory_make('fakesink')
        self.bin.set_property('video-sink', vsink)

    def __destroy_pipeline(self):
        if self.bin is None: return
        self.__set_gst_state(gst.STATE_NULL)
        bus = self.bin.get_bus()
        bus.disconnect(self.__bus_id)
        if self.__atf_id:
            self.bin.disconnect(self.__atf_id)
            self.__atf_id = None

        if self.__window is not None: self.__window.close()
        if self.__display is not None: self.__display.destroy()
        if self.__bus_video_id is not None:
            bus.disconnect(self.__bus_video_id)
        self.__bus_video_id = None
        self.__display = None
        self.__window = None

        bus.remove_signal_watch()
        del self.bin
        self.bin = None
        self.__bus_id = None

    def get_num_audio_channels(self):
        wanted_output = self.config.get('gstreamer', 'speaker_setup')
        if wanted_output == 'stereo':
            channels = 2
        elif wanted_output == '4channel':
            channels = 4
        elif wanted_output == '5channel':
            channels = 5
        elif wanted_output == '51channel':
            channels = 6
        elif wanted_output == 'ac3passthrough':
            channels = -1
        return channels

    def play(self):
        super(GstreamerPlayer, self).play()
        if not self._media_file: return
        if self.bin is None:
            self.__init_pipeline()

        def open_uri(uri, suburi = None):
            self.bin.set_property('uri', uri)
            if suburi is not None:
                self.bin.set_property('suburi', suburi)

            if self.__window is not None:
                self.__window.set_dpms(False)
            self.__set_gst_state(gst.STATE_PLAYING)

        if self._media_file["type"] == "webradio":
            while True:
                try: open_uri(self._media_file["uri"])
                except PlayerError, ex:
                    if self._media_file["url-index"] < \
                                            len(self._media_file["urls"])-1:
                        self._media_file["url-index"] += 1
                        self._media_file["uri"] = \
                                self._media_file["urls"]\
                                [self._media_file["url-index"]].encode("utf-8")
                    else:
                        raise ex
                else:
                    break
        else:
            suburi = None
            if self._has_external_subtitle():
                # external subtitle
                suburi = self._media_file["external_subtitle"]
            try: open_uri(self._media_file["uri"], suburi)
            except PlayerError, ex:
                raise ex

        self._init_video_information()

    def _player_set_alang(self,lang_idx):
        self.bin.set_property("current-audio", lang_idx)

    def _player_get_alang(self):
        return self.bin.get_property("current-audio")

    def _player_set_slang(self,lang_idx):
        if self._has_external_subtitle():
            return
        self.bin.set_property("current-text", lang_idx)

    def _player_get_slang(self):
        if self._has_external_subtitle():
            return SUB_EXTERNAL
        return self.bin.get_property("current-text")

    def _player_set_avoffset(self, offset):
        self.bin.set_property("av-offset", offset*1000000)

    def pause(self):
        if self.get_state() == PLAYER_PLAY:
            self.__set_gst_state(gst.STATE_PAUSED)
        elif self.get_state() == PLAYER_PAUSE:
            self.__set_gst_state(gst.STATE_PLAYING)
        else: return
        self.dispatch_signame('player.status')

    def _change_file(self,new_file):
        sig = self.get_state() == PLAYER_STOP and True or False
        self.__destroy_pipeline()
        self._media_file = new_file
        self.play()

        if self._media_file is not None:
            if sig: self.dispatch_signame('player.status')
            self.__current_change()

    def _set_volume(self, vol, sig=True):
        if self.bin is not None:
            v = float(vol)/100
            self.bin.set_property('volume', v)

    def get_position(self):
        if self.bin is not None and gst.STATE_NULL != self.__get_gst_state()\
                and self.bin.get_property('uri'):
            try: p = self.bin.query_position(gst.FORMAT_TIME)[0]
            except gst.QueryError: return 0
            p //= gst.SECOND
            return p
        return 0

    def _set_position(self,pos):
        if self.bin is not None and gst.STATE_NULL != self.__get_gst_state()\
                and self.bin.get_property('uri'):
            pos = max(0, int(pos))
            gst_time = pos * gst.SECOND

            event = gst.event_new_seek(
                1.0, gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH | \
                gst.SEEK_FLAG_ACCURATE, gst.SEEK_TYPE_SET, gst_time, \
                gst.SEEK_TYPE_NONE, 0)
            self.bin.send_event(event)

    def get_state(self):
        if self.bin is None: return PLAYER_STOP
        gst_state = self.__get_gst_state()
        if gst_state == gst.STATE_PLAYING:
            return PLAYER_PLAY
        elif gst_state == gst.STATE_PAUSED:
            return PLAYER_PAUSE
        else:
            return PLAYER_STOP

    def __set_gst_state(self, gst_state):
        state_ret = self.bin.set_state(gst_state)
        timeout = 5

        while state_ret == gst.STATE_CHANGE_ASYNC and timeout > 0:
            state_ret,state,pending_state = self.bin.get_state(1*gst.SECOND)
            timeout -= 1

            if state_ret != gst.STATE_CHANGE_SUCCESS:
                raise PlayerError(_("Unable to change gstreamer state"))


    def __get_gst_state(self):
        # changestatus,state,_state
        return self.bin.get_state()[1]

    def __sync_message(self, bus, message):
        if message.structure is None:
            return
        message_name = message.structure.get_name()
        if message_name == 'prepare-xwindow-id':
            if self.__window is None:
                if self._video_options["fullscreen"]:
                    self.__window = x11.X11Window(self.__display,\
                            fullscreen = True)
                else:
                    self.__window = x11.X11Window(self.__display,\
                            width=400, height=200)

            imagesink = message.src
            imagesink.set_property("force-aspect-ratio","true")
            imagesink.set_xwindow_id(self.__window.window_p())

    def __about_to_finish(self, pipeline):
        if self._media_file["type"] != "webradio":
            self.__new_file = self._source.next(explicit = False)
            if self.__new_file is not None and \
                    not self.__need_pipeline_change(self.__new_file):
                # we can enter in a gapless transition
                self.__in_gapless_transition = True

                # set new uri and suburi if necessary:
                self.bin.set_property('uri', self.__new_file["uri"])
                if self._has_external_subtitle():
                    # external subtitle
                    suburi = self._new_file["external_subtitle"]
                    self.bin.set_property('suburi', suburi)

        return True

    def __message(self, bus, message):
        if message.type == gst.MESSAGE_EOS:
            if self._media_file is not None and \
                    self._media_file["type"] == "webradio":
                # an error happened, try the next url
                if self._media_file["url-index"] \
                        < len(self._media_file["urls"])-1:
                    self._media_file["url-index"] += 1
                    self._media_file["uri"] = \
                            self._media_file["urls"]\
                                [self._media_file["url-index"]].encode("utf-8")
                    self.play()
                return False
            self._end()
        elif message.type == gst.MESSAGE_TAG:
            if self._media_file and self._media_file["type"] == "webradio":
                self.__update_metadata(message.parse_tag())
        elif message.type == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            err = str(err).decode("utf8", 'replace')
            log.err("Gstreamer : " + err)
        elif message.type == gst.MESSAGE_ELEMENT:
            name = ""
            if hasattr(message.structure, "get_name"):
                name = message.structure.get_name()

            # This gets sent on song change. But it is not in the docs
            if name == "playbin2-stream-changed" \
                    and self.__in_gapless_transition:
                self._end()

        return True

    def _end(self):
        try: self._media_file.played()
        except AttributeError:
            pass
        else:
            for plugin in self.plugins:
                plugin.on_media_played(self._media_file)

        if self.__in_gapless_transition:
            self._media_file = self.__new_file
            self._init_video_information()
            self.__current_change()
            self.__in_gapless_transition = False
        else:
            self._change_file(self._source.next(explicit = False))

    def __update_metadata(self, tags):
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
        self.dispatch_signame('player.current')

    def __need_pipeline_change(self, new_file):
        return self._media_file["type"] != new_file["type"]

    def __current_change(self):
        # replaygain reset
        self.set_volume(self.get_volume(), sig=False)

        self.dispatch_signame('player.current')

    def _osd_set(self, text):
        if not self.__osd: return
        self.__osd.set_property("text", text)
        self.__osd.set_property("silent", False)

        reactor.callLater(2, self._osd_hide)

    def _osd_hide(self):
        if self.__osd:
            self.__osd.set_property("silent", True)

    # Functions used by library to known supported formats
    def is_supported_uri(self,uri_type):
        t = uri_type+"://"
        return gst.element_make_from_uri(gst.URI_SRC, t, '')  is not None

    SUPPORTED_MIME_TYPES = None
    def is_supported_format(self,format):
        if self.SUPPORTED_MIME_TYPES is None:
            self.SUPPORTED_MIME_TYPES = []
            factories = gst.type_find_factory_get_list()
            for factory in factories:
                if factory.get_name() in ("video/mpeg4", "video/x-h264"):
                    # FIXME for this 2 factories, returned mimetype is strange
                    # in debian squeeze
                    self.SUPPORTED_MIME_TYPES.append(factory.get_name())
                caps = factory.get_caps()
                if caps is None:
                    continue
                for c in caps:
                    self.SUPPORTED_MIME_TYPES.append(c.get_name())

        formats = {
            ".mp3": ("audio/mpeg",),
            ".mp2": ("audio/mpeg",),
            ".ogg": ("application/ogg", "audio/x-vorbis", "video/x-theora"),
            ".m4a": ("audio/x-m4a",),
            ".flac": ("audio/x-flac",),
            ".avi": ("video/x-msvideo",),
            ".mp4": ("video/x-h264", "audio/x-m4a"),
            ".mkv": ("video/x-matroska",),
            ".m4v": ("video/x-h264",),
            }

        if format in formats.keys():
            for mime in formats[format]:
                if mime not in self.SUPPORTED_MIME_TYPES:
                    return False
            return True

        return False

# vim: ts=4 sw=4 expandtab
