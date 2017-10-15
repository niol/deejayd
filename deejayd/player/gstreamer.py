# Deejayd, a media player daemon
# Copyright (C) 2007-2017 Mickael Royer <mickael.royer@gmail.com>
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
from deejayd.jsonrpc.interfaces import jsonrpc_module, PlayerModule
from deejayd.player import PlayerError
from deejayd.player._base import _BasePlayer, PLAYER_PAUSE, \
                                 PLAYER_PLAY, PLAYER_STOP
from deejayd.ui import log
from pytyx11 import x11

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import GObject, GLib, Gst
from gi.repository import GstVideo # needed for xvimagesink.set_window_handle()
from deejayd.player._gstutils import TagListWrapper, parse_gstreamer_taglist
GObject.threads_init()
Gst.init(None)


SUB_EXTERNAL = 0


@jsonrpc_module(PlayerModule)
class GstreamerPlayer(_BasePlayer):
    NAME = 'gstreamer'
    supported_options = ("current-audio", "current-sub", "av-offset",)

    def __init__(self, config):
        super(GstreamerPlayer, self).__init__(config)
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

    def __gst_add_elts_to_sink(self, sink_bin, elts, test_preroll=True):
        for elt in elts:
            sink_bin.add(elt)
        try:
            linked_result = None
            for elt in elts:
                if linked_result is not None:
                    linked_result.link(elt)
                linked_result = elt
        except Exception as e:
            err = str(e).decode("utf8", 'replace')
            raise PlayerError(_("Could not link GStreamer pipeline: '%s'")
                               % err)
        # Test to ensure output pipeline can preroll
        if test_preroll:
            sink_bin.set_state(Gst.State.READY)
            result, state, pending = sink_bin.get_state(timeout=Gst.SECOND / 2)
            if result == Gst.StateChangeReturn.FAILURE:
                sink_bin.set_state(Gst.State.NULL)
                raise PlayerError(_("Unable to create pipeline"))

    def __open_audio_sink(self):
        # Open a Audio sink
        # [<-> Ghospad -> audiofilter -> audioconvert -> audioresample
        # -> audio sink]
        audio_sink_bin = Gst.Pipeline()
        audiofilter = Gst.ElementFactory.make('capsfilter', None)
        audioconvert = Gst.ElementFactory.make('audioconvert', None)
        audioresample = Gst.ElementFactory.make('audioresample', None)
        try:
            audio_sink = Gst.parse_launch(self.__gst_options["audio_p"])
            ret = audio_sink.set_state(Gst.State.READY)
            if ret == Gst.StateChangeReturn.FAILURE:
                raise PlayerError
        except (PlayerError, GObject.GError) as err:
            raise PlayerError(_("No audio sink found for Gstreamer : %s")
                              % str(err).decode("utf8", 'replace'))
        finally:
            try:
                audio_sink.set_state(Gst.State.NULL)
            except:
                pass

        # playbin has started to control the volume through pulseaudio,
        # which means the volume property can change without us noticing.
        # Use our own volume element for now until this works with PA.
        self.__vol_element = Gst.ElementFactory.make('volume', None)
        try:
            self.__gst_add_elts_to_sink(audio_sink_bin,
                                        [self.__vol_element, audiofilter,
                                         audioconvert, audioresample,
                                         audio_sink])
        except PlayerError as ex:
            self.__destroy_pipeline()
            raise ex
        # create ghostpad
        audio_sink_bin.add_pad(Gst.GhostPad.new('sink',
                                                self.__vol_element.
                                                get_static_pad('sink')))

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

        return audio_sink_bin

    def _open_display(self):
        d_list = [self._video_options["display"]]
        if "DISPLAY" in os.environ:
            d_list.append(os.environ["DISPLAY"])
        for d in d_list:
            try:
                self.__display = x11.X11Display(d_id=d)
            except x11.X11Error:
                continue
            else:
                self.__display.set_dpms(False)
                return
        raise PlayerError(_("Unable to open video display"))

    def __open_video_sink(self):
        # [<-> Ghospad -> textoverlay (for OSD support) -> video sink]
        try:
            video_sink = Gst.parse_launch(self.__gst_options["video_p"])
            ret = video_sink.set_state(Gst.State.READY)
            if ret == Gst.StateChangeReturn.FAILURE:
                raise PlayerError
        except (PlayerError, GObject.GError) as err:
            self.__destroy_pipeline()
            raise PlayerError(_("No video sink found for Gstreamer : %s")
                              % str(err).decode("utf8", 'replace'))

        bufbin = Gst.Pipeline()
        self.__osd = Gst.ElementFactory.make('textoverlay', None)
        self.__osd.set_property("silent", True)
        self.__osd.set_property("halignment", 0)  # left
        self.__osd.set_property("valignment", 2)  # top
        try:
            self.__gst_add_elts_to_sink(bufbin, [self.__osd, video_sink])
        except PlayerError as ex:
            self.__destroy_pipeline()
            raise ex
        # create ghostpad
        gpad = Gst.GhostPad.new('sink', self.__osd.get_static_pad('video_sink'))
        bufbin.add_pad(gpad)
        return bufbin

    def __init_pipeline(self):
        if self.bin is not None:
            return

        self.bin = Gst.ElementFactory.make('playbin', None)
        self.bin.set_property("auto-flush-bus", True)

        if self.__gst_options["audio_p"] != "fakesink":
            audio_sink_bin = self.__open_audio_sink()
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
        if self._playing_media.has_video() \
                and self.__gst_options["video_p"] != "fakesink":
            self._open_display()
            # init X11 window if not exist
            if self.__window is None:
                if self._video_options["fullscreen"]:
                    self.__window = x11.X11Window(self.__display,
                                                  fullscreen=True)
                else:
                    self.__window = x11.X11Window(self.__display,
                                                  width=400, height=200)
            # disable OSD for now, gstreamer stuck at PREROLLING state
            # if it is enabled
            #vsink = self.__open_video_sink()
            vsink = Gst.parse_launch(self.__gst_options["video_p"])
            bus.enable_sync_message_emission()
            self.__bus_video_id = bus.connect('sync-message::element',
                                              self.__sync_message)
        else:
            vsink = Gst.ElementFactory.make('fakesink', None)
        self.bin.set_property('video-sink', vsink)

    def __destroy_pipeline(self):
        if self.bin is None:
            return
        self.__set_gst_state(Gst.State.NULL)
        bus = self.bin.get_bus()
        if self.__bus_id is not None:
            bus.disconnect(self.__bus_id)
            self.__bus_id = None
        if self.__atf_id is not None:
            self.bin.disconnect(self.__atf_id)
            self.__atf_id = None

        if self.__window is not None:
            self.__window.close()
        if self.__display is not None:
            self.__display.destroy()
        if self.__bus_video_id is not None:
            bus.disconnect(self.__bus_video_id)
            self.__bus_video_id = None
        self.__display = None
        self.__window = None

        bus.remove_signal_watch()
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
        else:
            raise PlayerError(_("'%s' is not allowed for speaker_setup "
                                "option") % wanted_output)
        return channels

    def play(self):
        def open_uri(uri, suburi=None):
            self.bin.set_property('uri', uri)
            if suburi is not None:
                self.bin.set_property('suburi', suburi)

            if self.__display is not None:
                self.__display.set_dpms(False)

        if not self._playing_media:
            return
        self.__init_pipeline()
        playing = False
        uris = iter(self._playing_media.get_uris())
        try:
            while not playing:
                uri = next(uris)
                self.bin.set_property('uri', uri)
                if self._playing_media.has_video() \
                        and "external_subtitle" in self._playing_media:
                    suburi = self._playing_media["external_subtitle"]
                    self.bin.set_property('suburi', suburi)
                try:
                    self.__set_gst_state(Gst.State.PLAYING)
                except PlayerError:
                    continue
                else:
                    playing = True
        except StopIteration:
            raise PlayerError(_("unable to play file "
                                "%s") % self._playing_media['title'])

    def _player_set_alang(self, lang_idx):
        self.bin.set_property("current-audio", lang_idx)

    def _player_get_alang(self):
        return self.bin.get_property("current-audio")

    def _player_set_slang(self, lang_idx):
        for ch in self._playing_media["sub_channels"]:
            if ch["idx"] == lang_idx:
                if not ch["is_external"]:               
                    self.bin.set_property("current-text", lang_idx)

    def _player_get_slang(self):
        return self.bin.get_property("current-text")

    def _player_set_avoffset(self, offset):
        self.bin.set_property("av-offset", offset * 1000000)

    def pause(self):
        if self.get_state() == PLAYER_PLAY:
            self.__set_gst_state(Gst.State.PAUSED)
        elif self.get_state() == PLAYER_PAUSE:
            self.__set_gst_state(Gst.State.PLAYING)
        else:
            return
        self.dispatch_signame('player.status')

    def _change_file(self, new_file):
        self.__destroy_pipeline()
        self._playing_media = new_file
        self.play()

        if self._playing_media is not None:
            self.__current_change()
        self.dispatch_signame('player.status')
        self.dispatch_signame('player.current')

    def _set_volume(self, vol, sig=True):
        if self.__vol_element is not None:
            v = float(vol) / 100
            self.__vol_element.set_property('volume', v)

    def get_position(self):
        if self.bin is not None and Gst.State.NULL != self.__get_gst_state()\
                and self.bin.get_property('current-uri'):
            ok, p = self.bin.query_position(Gst.Format.TIME)
            if not ok:
                log.err(_("Gstreamer: unable to get stream position"))
                return 0
            p //= Gst.SECOND
            return p
        return 0

    def _set_position(self, pos):
        if self.bin is not None and Gst.State.NULL != self.__get_gst_state()\
                and self.bin.get_property('current-uri'):
            pos = max(0, int(pos))
            self.bin.seek_simple(Gst.Format.TIME,
                                 Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                 pos*Gst.SECOND)

    def get_state(self):
        if self.bin is None:
            return PLAYER_STOP
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
            state_ret, state, pending_state = self.bin.get_state(
                timeout=1*Gst.SECOND)
            timeout -= 1

        if state_ret != Gst.StateChangeReturn.SUCCESS:
            raise PlayerError(_("Unable to change gstreamer state"))

    def __get_gst_state(self):
        # changestatus,state,_state
        return self.bin.get_state(timeout=1*Gst.SECOND)[1]

    def __sync_message(self, bus, message):
        structure = message.get_structure()
        if structure is None:
            return
        message_name = structure.get_name()
        if message_name == 'prepare-window-handle':
            message.src.set_property("force-aspect-ratio", "true")
            message.src.set_window_handle(self.__window.window_p())

    def __about_to_finish(self, pipeline):
        if self._playing_media is None:
            return

        if self._playing_media.is_seekable():
            self.__in_gapless_transition = True
            self.__new_file = self._source.next(explicit=False)
            if self.__new_file is not None and \
                    not self.__need_pipeline_change(self.__new_file):
                # set new uri and suburi if necessary:
                self.bin.set_property('uri', self.__new_file["uri"])
                if self.__new_file.has_video():
                    suburi = self.__new_file["external_subtitle"]
                    self.bin.set_property('suburi', suburi)

    def __message(self, bus, message):
        if message.type == Gst.MessageType.EOS:
            self._end()
        elif message.type == Gst.MessageType.TAG:
            self.__update_metadata(message.parse_tag())
        elif message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            log.err("Gstreamer Error: %s" % str(err))
            log.debug("Gstreamer Error debug: %s" % str(debug))
        elif message.type == Gst.MessageType.STREAM_START:
            if self.__in_gapless_transition:
                self._end()
        return True

    def _end(self):
        if self._playing_media is not None:
            if self._playing_media.is_seekable():
                self._playing_media.played()

            if self.__in_gapless_transition:
                self._playing_media = self.__new_file
                self.__current_change()
                self.__in_gapless_transition = False
                self.dispatch_signame('player.status')
                self.dispatch_signame('player.current')
            else:
                self._change_file(self._source.next(explicit=False))

    def __update_metadata(self, tags):
        tags = TagListWrapper(tags)
        tags = parse_gstreamer_taglist(tags)

        if "title" in tags:
            desc = tags["title"][0]
            if "artist" in tags:
                desc = tags["artist"][0] + " - " + desc
            self._playing_media.set_description(desc)
            self.dispatch_signame('player.current')

    def __need_pipeline_change(self, new_file):
        return self._playing_media.has_video() != new_file.has_video()

    def __current_change(self):
        # replaygain reset
        self.set_volume(self.get_volume(), sig=False)

    def _osd_set(self, text):
        if self.__osd is not None:
            self.__osd.set_property("text", text)
            self.__osd.set_property("silent", False)

            reactor.callLater(2, self._osd_hide)

    def _osd_hide(self):
        if self.__osd is not None:
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


def init(config):
    # Enable error messages by default
    if Gst.debug_get_default_threshold() == Gst.DebugLevel.NONE:
        Gst.debug_set_default_threshold(Gst.DebugLevel.ERROR)

    if Gst.Element.make_from_uri(
            Gst.URIType.SRC, "file:///fake/path/for/gst", ""):
        return GstreamerPlayer(config)
    else:
        raise PlayerError(
            _("Unable to open input files"),
            _("GStreamer has no element to handle reading files. Check "
                "your GStreamer installation settings."))
