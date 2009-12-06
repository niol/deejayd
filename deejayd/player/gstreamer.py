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

    def __init__(self, db, plugin_manager, config):
        UnknownPlayer.__init__(self, db, plugin_manager, config)
        self.__volume = 100

        # Open a Audio pipeline
        pipeline =  self.config.get("gstreamer", "audio_output")
        if pipeline in ("gconf", "auto"):
            pipeline += "audiosink"
        else:
            pipeline += "sink"
        try: audio_sink = gst.parse_launch(pipeline)
        except gobject.GError, err:
            raise PlayerError(_("No audio sink found for Gstreamer : %s"%err))

        # More audio-sink option
        if pipeline == "alsasink":
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
        raise NotImplementedError

    def on_message(self, bus, message):
        if message.type == gst.MESSAGE_EOS:
            if self._media_file["type"] == "webradio":
                # an error happened, try the next url
                if self._media_file["url-index"] \
                        < len(self._media_file["urls"])-1:
                    self._media_file["url-index"] += 1
                    self._media_file["uri"] = \
                            self._media_file["urls"]\
                                [self._media_file["url-index"]].encode("utf-8")
                    self.start_play()
                return False
            elif self._media_file:
                try: self._media_file.played()
                except AttributeError: pass
                for plugin in self.plugins:
                    plugin.on_media_played(self._media_file)
            self._change_file(self._source.next(explicit = False))
        elif message.type == gst.MESSAGE_TAG:
            self._update_metadata(message.parse_tag())
        elif message.type == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            err = str(err).decode("utf8", 'replace')
            log.err("Gstreamer : " + err)

        return True

    def start_play(self):
        super(GstreamerPlayer, self).start_play()
        if not self._media_file: return

        def open_uri(uri):
            self.bin.set_property('uri',uri)
            state_ret = self.bin.set_state(gst.STATE_PLAYING)
            timeout = 4
            state = None

            while state_ret == gst.STATE_CHANGE_ASYNC and timeout > 0:
                state_ret,state,pending_state = self.bin.get_state(1 * gst.SECOND)
                timeout -= 1

            if state_ret != gst.STATE_CHANGE_SUCCESS:
                msg = _("Unable to play file %s") % uri
                raise PlayerError(msg)

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
            try: open_uri(self._media_file["uri"])
            except PlayerError, ex:
                self._destroy_stream()
                raise ex

    def pause(self):
        if self.get_state() == PLAYER_PLAY:
            self.bin.set_state(gst.STATE_PAUSED)
        elif self.get_state() == PLAYER_PAUSE:
            self.bin.set_state(gst.STATE_PLAYING)
        else: return
        self.dispatch_signame('player.status')

    def stop(self,widget = None, event = None):
        self._media_file = None
        self.bin.set_state(gst.STATE_NULL)
        # FIXME : try to remove this one day ...
        self._source.queue_reset()

        self.dispatch_signame('player.status')

    def _change_file(self,new_file):
        sig = self.get_state() == PLAYER_STOP and True or False
        self.stop()
        self._media_file = new_file
        self.start_play()

        # replaygain reset
        self.set_volume(self.__volume, sig=False)

        if sig: self.dispatch_signame('player.status')
        self.dispatch_signame('player.current')

    def get_volume(self):
        return self.__volume

    def set_volume(self, vol, sig=True):
        self.__volume = min(100, int(vol))
        v = float(self.__volume)/100
        # replaygain support
        if self._replaygain and self._media_file is not None:
            try: scale = self._media_file.replay_gain()
            except AttributeError: pass # replaygain not supported
            else:
                v = max(0.0, min(4.0, v * scale))
                v = float(min(100, int(v * 100)))/100
        self.bin.set_property('volume', v)
        if sig: self.dispatch_signame('player.status')

    def get_position(self):
        if gst.STATE_NULL != self.__get_gst_state() and \
                self.bin.get_property('uri'):
            try: p = self.bin.query_position(gst.FORMAT_TIME)[0]
            except gst.QueryError: return 0
            p //= gst.SECOND
            return p
        return 0

    def _set_position(self,pos):
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
        self.dispatch_signame('player.current')

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
        if uri_type == "dvd": return False
        return gst.element_make_from_uri(gst.URI_SRC,uri_type+"://", '') \
                    is not None

    def is_supported_format(self,format):
        formats = {
            ".mp3": ("mad",),
            ".mp2": ("mad",),
            ".ogg": ("ogg", "vorbis"),
            ".mp4": ("faad",),
            ".flac": ("flac",),
            }

        if format in formats.keys():
            for plugin in formats[format]:
                if gst.registry_get_default().find_plugin(plugin) == None:
                    return False
            return True

        return False

# vim: ts=4 sw=4 expandtab
