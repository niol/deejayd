# Deejayd, a media player daemon
# Copyright (C) 2007-2013 Mickael Royer <mickael.royer@gmail.com>
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

import os, threading
from twisted.internet import reactor

# gstreamer >= 1.0 import
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, GLib, Gst, GstVideo
GObject.threads_init()
Gst.init(None)

# Gst.SECOND is broken
SECOND = 1000000000

from deejayd.jsonrpc.interfaces import jsonrpc_module, PlayerModule
from deejayd.player import PlayerError
from deejayd.player._base import *
from deejayd.player._gstutils import *
from deejayd.ui import log
from pytyx11 import x11

SUB_EXTERNAL = 0

@jsonrpc_module(PlayerModule)
class GstreamerPlayer(_BasePlayer):
    NAME = 'gstreamer'
    supported_options = ("audio_lang", "sub_lang", "av_offset",)

    def __init__(self, plugin_manager, config):
        super(GstreamerPlayer, self).__init__(plugin_manager, config)
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
        self.__vol_element = None

    def __gst_add_elts_to_sink(self, sink_bin, elts):
        for elt in elts: sink_bin.add(elt)
        try:
            linked_result = None
            for elt in elts:
                if linked_result is not None:
                    linked_result.link(elt)
                linked_result = elt
        except Exception, e:
            err = str(e).decode("utf8", 'replace')
            raise PlayerError(_("Could not link GStreamer pipeline: '%s'")\
                               % err)
        # Test to ensure output pipeline can preroll
        sink_bin.set_state(Gst.State.READY)
        result, state, pending = sink_bin.get_state(timeout=SECOND / 2)
        if result == Gst.StateChangeReturn.FAILURE:
            sink_bin.set_state(Gst.State.NULL)
            raise PlayerError(_("Unable to create pipeline"))

    def __init_pipeline(self):
        if self.bin is not None: return

        self.bin = Gst.ElementFactory.make('playbin', None)
        self.bin.set_property("auto-flush-bus", True)

        if self.__gst_options["audio_p"] != "fakesink":
            # Open a Audio sink
            # [<-> Ghospad -> audiofilter -> audioconvert -> audioresample
            # -> audio sink]
            audio_sink_bin = Gst.Bin()
            audiofilter = Gst.ElementFactory.make('capsfilter', None)
            audioconvert = Gst.ElementFactory.make('audioconvert', None)
            audioresample = Gst.ElementFactory.make('audioresample', None)
            try:
                audio_sink = Gst.parse_launch(self.__gst_options["audio_p"])
                ret = audio_sink.set_state(Gst.State.READY)
                if ret == Gst.StateChangeReturn.FAILURE:
                    raise PlayerError
            except (PlayerError, GObject.GError), err:
                raise PlayerError(_("No audio sink found for Gstreamer : %s") \
                        % str(err).decode("utf8", 'replace'))
            finally:
                try: audio_sink.set_state(Gst.State.NULL)
                except:
                    pass

            # playbin2 has started to control the volume through pulseaudio,
            # which means the volume property can change without us noticing.
            # Use our own volume element for now until this works with PA.
            self.__vol_element = Gst.ElementFactory.make('volume', None)
            try:
                self.__gst_add_elts_to_sink(audio_sink_bin, \
                     [self.__vol_element, audiofilter, audioconvert,\
                      audioresample, audio_sink])
            except PlayerError, ex:
                self.__destroy_pipeline()
                raise ex
            # create ghostpad
            audio_sink_bin.add_pad(Gst.GhostPad.new('sink',
                                   self.__vol_element.get_static_pad('sink')))

            wanted_channels = self.get_num_audio_channels()
            if wanted_channels != -1:
                wanted_caps = Gst.Caps.new_empty()

                audio_sink_caps = audio_sink.get_static_pad('sink').query_caps(None)
                for i in range(audio_sink_caps.get_size()):
                    cap = audio_sink_caps.get_structure(i)
                    if cap.has_field("channels"):
                        wanted_cap = cap.copy()
                        wanted_cap.set_value("channels", wanted_channels)
                        wanted_caps.append_structure(wanted_cap)

                audiofilter.set_property('caps', wanted_caps)
        else:
            audio_sink_bin = Gst.ElementFactory.make('fakesink', None)
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
            try: video_sink = Gst.parse_launch(self.__gst_options["video_p"])
            except GObject.GError, err:
                self.__destroy_pipeline()
                raise PlayerError(_("No video sink found for Gstreamer : %s") \
                        % str(err).decode("utf8", 'replace'))

            def open_display(d):
                try: self.__display = x11.X11Display(id=d)
                except x11.X11Error:
                    raise PlayerError(_("Unable to open video display"))

            if self.__gst_options["video_p"] != "fakesink":
                try: open_display(self._video_options["display"])
                except PlayerError, ex:  # try to get display with env var
                    try: open_display(os.environ["DISPLAY"])
                    except (PlayerError, KeyError):
                        self.__destroy_pipeline()
                        raise ex

                bus.enable_sync_message_emission()
                self.__bus_video_id = bus.connect('sync-message::element', \
                                                  self.__sync_message)

            bufbin = Gst.Bin()
            self.__osd = Gst.ElementFactory.make('textoverlay', None)
            self.__osd.set_property("silent", True)
            self.__osd.set_property("halignment", 0)  # left
            self.__osd.set_property("valignment", 2)  # top
            bin_elts = [self.__osd, video_sink]
            try:
                self.__gst_add_elts_to_sink(bufbin, bin_elts)
            except PlayerError, ex:
                self.__destroy_pipeline()
                raise ex
            # create ghostpad
            gpad = Gst.GhostPad.new('sink', self.__osd.get_static_pad('video_sink'))
            bufbin.add_pad(gpad)
            vsink = bufbin
        else:
            vsink = Gst.ElementFactory.make('fakesink', None)
        self.bin.set_property('video-sink', vsink)

    def __destroy_pipeline(self):
        if self.bin is None: return
        self.__set_gst_state(Gst.State.NULL)
        bus = self.bin.get_bus()
        if self.__bus_id is not None:
            bus.disconnect(self.__bus_id)
            self.__bus_id = None
        if self.__atf_id is not None:
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

        self.__vol_element = None

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

        def open_uri(uri, suburi=None):
            self.bin.set_property('uri', uri)
            if suburi is not None:
                self.bin.set_property('suburi', suburi)

            if self.__window is not None:
                self.__window.set_dpms(False)
            self.__set_gst_state(Gst.State.PLAYING)

        if self._media_file["type"] == "webradio":
            while True:
                try: open_uri(self._media_file["uri"])
                except PlayerError, ex:
                    if self._media_file["url-index"] < \
                                            len(self._media_file["urls"]) - 1:
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

    def _player_set_alang(self, lang_idx):
        self.bin.set_property("current-audio", lang_idx)

    def _player_get_alang(self):
        return self.bin.get_property("current-audio")

    def _player_set_slang(self, lang_idx):
        if self._has_external_subtitle():
            return
        self.bin.set_property("current-text", lang_idx)

    def _player_get_slang(self):
        if self._has_external_subtitle():
            return SUB_EXTERNAL
        return self.bin.get_property("current-text")

    def _player_set_avoffset(self, offset):
        self.bin.set_property("av-offset", offset * 1000000)

    def pause(self):
        if self.get_state() == PLAYER_PLAY:
            self.__set_gst_state(Gst.State.PAUSED)
        elif self.get_state() == PLAYER_PAUSE:
            self.__set_gst_state(Gst.State.PLAYING)
        else: return
        self.dispatch_signame('player.status')

    def _change_file(self, new_file):
        self.__destroy_pipeline()
        self._media_file = new_file
        self.play()

        if self._media_file is not None:
            self.dispatch_signame('player.status')
            self.__current_change()
        self.dispatch_signame('player.current')

    def _set_volume(self, vol, sig=True):
        if self.bin is not None:
            v = float(vol) / 100
            self.__vol_element.set_property('volume', v)

    def get_position(self):
        if self.bin is not None and Gst.State.NULL != self.__get_gst_state()\
                and self.bin.get_property('current-uri'):
            ok, p = self.bin.query_position(Gst.Format.TIME)
            if not ok:
                log.err(_("Gstreamer: unable to get stream position"))
                return 0
            p //= SECOND
            return p
        return 0

    def _set_position(self, pos):
        if self.bin is not None and Gst.State.NULL != self.__get_gst_state()\
                and self.bin.get_property('current-uri'):
            pos = max(0, int(pos))
            self.bin.seek_simple(Gst.Format.TIME,
                Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, pos*Gst.SECOND)

    def get_state(self):
        if self.bin is None: return PLAYER_STOP
        gst_state = self.__get_gst_state()
        if gst_state == Gst.State.PLAYING:
            return PLAYER_PLAY
        elif gst_state == Gst.State.PAUSED:
            return PLAYER_PAUSE
        else:
            return PLAYER_STOP

    def __set_gst_state(self, gst_state):
        state_ret = self.bin.set_state(gst_state)
        timeout = 5

        while state_ret == Gst.StateChangeReturn.ASYNC and timeout > 0:
            state_ret, state, pending_state = self.bin.get_state(1 * SECOND)
            timeout -= 1

            if state_ret != Gst.StateChangeReturn.SUCCESS:
                raise PlayerError(_("Unable to change gstreamer state"))


    def __get_gst_state(self):
        # changestatus,state,_state
        return self.bin.get_state(1 * SECOND)[1]

    def __sync_message(self, bus, message):
        structure = message.get_structure()
        if structure is None:
            return
        message_name = structure.get_name()
        if message_name == 'prepare-window-handle':
            if self.__window is None:
                if self._video_options["fullscreen"]:
                    self.__window = x11.X11Window(self.__display, \
                            fullscreen=True)
                else:
                    self.__window = x11.X11Window(self.__display, \
                            width=400, height=200)

            imagesink = message.src
            imagesink.set_property("force-aspect-ratio", "true")
            imagesink.set_window_handle(self.__window.window_p())

    def __about_to_finish(self, pipeline):
        if self._media_file is None or self._media_file["type"] == "webradio":
            return

        self.__in_gapless_transition = True
        self.__new_file = self._source.next(explicit=False)
        if self.__new_file is not None and \
                not self.__need_pipeline_change(self.__new_file):
            # set new uri and suburi if necessary:
            self.bin.set_property('uri', self.__new_file["uri"])
            if self._has_external_subtitle(self.__new_file):
                # external subtitle
                suburi = self.__new_file["external_subtitle"]
                self.bin.set_property('suburi', suburi)

    def __message(self, bus, message):
        if message.type == Gst.MessageType.EOS:
            print "receive EOS message"
            if self._media_file is not None and \
                    self._media_file["type"] == "webradio":
                # an error happened, try the next url
                if self._media_file["url-index"] \
                        < len(self._media_file["urls"]) - 1:
                    self._media_file["url-index"] += 1
                    self._media_file["uri"] = \
                            self._media_file["urls"]\
                                [self._media_file["url-index"]].encode("utf-8")
                    self.play()
                return False
            self._end()
        elif message.type == Gst.MessageType.TAG:
            if self._media_file and self._media_file["type"] == "webradio":
                self.__update_metadata(message.parse_tag())
        elif message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            err = str(err).decode("utf8", 'replace')
            log.err("Gstreamer Error: %s" % err)
            debug = str(debug).decode("utf8", 'replace')
            log.debug("Gstreamer Error debug: %s" % debug)
        elif message.type == Gst.MessageType.STREAM_START:
            if self.__in_gapless_transition:
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
            self.dispatch_signame('player.status')
            self.dispatch_signame('player.current')
        else:
            self._change_file(self._source.next(explicit=False))

    def __update_metadata(self, tags):
        tags = TagListWrapper(tags)
        tags = parse_gstreamer_taglist(tags)

        if "title" in tags.keys():
            desc = tags["title"]
            if "artist" in tags.keys():
                desc = tags["artist"] + " - " + desc
            self._media_file["webradio-desc"] = desc
            self.dispatch_signame('player.current')

    def __need_pipeline_change(self, new_file):
        return self._media_file["type"] != new_file["type"]

    def __current_change(self):
        # replaygain reset
        self.set_volume(self.get_volume(), sig=False)

    def _osd_set(self, text):
        if not self.__osd: return
        self.__osd.set_property("text", text)
        self.__osd.set_property("silent", False)

        reactor.callLater(2, self._osd_hide)

    def _osd_hide(self):
        if self.__osd:
            self.__osd.set_property("silent", True)

    # Function to know if we able to play webradio
    def is_supported_uri(self, uri_type):
        uri = uri_type + "://"
        if not Gst.uri_is_valid(uri):
            return False
        try:
            Gst.Element.make_from_uri(Gst.URIType.SRC, uri, '')
        except GLib.GError:
            return False
        return True


def init(plugin_manager, config):
    # Enable error messages by default
    if Gst.debug_get_default_threshold() == Gst.DebugLevel.NONE:
        Gst.debug_set_default_threshold(Gst.DebugLevel.ERROR)

    if Gst.Element.make_from_uri(
        Gst.URIType.SRC,
        "file:///fake/path/for/gst", ""):
        return GstreamerPlayer(plugin_manager, config)
    else:
        raise PlayerError(
            _("Unable to open input files"),
            _("GStreamer has no element to handle reading files. Check "
                "your GStreamer installation settings."))

# vim: ts=4 sw=4 expandtab
