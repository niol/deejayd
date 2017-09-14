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

from deejayd.common.component import SignalingComponent, JSONRpcComponent
from deejayd.common.component import PersistentStateComponent
from deejayd.player import PlayerError


__all__ = ['PLAYER_PLAY', 'PLAYER_PAUSE', 'PLAYER_STOP', '_BasePlayer']

PLAYER_PLAY = "play"
PLAYER_PAUSE = "pause"
PLAYER_STOP = "stop"


class _BasePlayer(SignalingComponent, JSONRpcComponent,
                  PersistentStateComponent):
    state_name = "player"
    # initial value for player state
    initial_state = {
        "volume": {"song": 100, "video": 100, "webradio": 100},
        "state": "stop",
        "current": -1,
        "current_source": "none",
        "current_pos": 0,
    }
    options = (
        "current-audio",
        "current-sub",
        "av-offset",
        "sub-offset",
        "zoom",
        "aspect-ratio"
    )
    aspect_ratios = (
        "auto",
        "1:1",
        "4:3",
        "16:9",
        "16:10",
        "221:100",
        "235:100",
        "239:100",
        "5:4"
    )
    supported_options = []
    default_channels = []

    def __init__(self, config):
        super(_BasePlayer, self).__init__()
        self.config = config
        # Initialise var
        self._source = None
        self._playing_media = None
        self._replaygain = config.getboolean("general", "replaygain")
        self._replaygain_opts = {
            "profiles": config.getlist("general", "replaygain_profiles"),
            "preamp_gain": config.getfloat("general", "pre_amp_gain"),
            "fallback_gain": config.getfloat("general", "fallback_gain"),
        }

        # get video options
        self.video_enable = config.getboolean("video", "enabled")
        self._video_options = {
                "display": self.config.get("video", "display"),
                "fullscreen": self.config.getboolean("video", "fullscreen"),
                "osd": self.config.getboolean("video", "osd_support"),
                "osd_size": self.config.getint("video", "osd_font_size"),
            }
        self.load_state()

    def load_state(self):
        super(_BasePlayer, self).load_state()
        # Restore volume
        self.__volume = self.state["volume"]

        # Restore current media
        media_pos = int(self.state["current"])
        source = self.state["current_source"]
        if media_pos != -1 and source not in ("audioqueue", "none"):
            self._playing_media = self._source.go_to(media_pos, "pos", source)

        # Update playing state
        playing_state = self.state["state"]
        if playing_state != PLAYER_STOP and self._playing_media is not None:
            try:
                self.play()
            except PlayerError:
                # There is an issue restoring the playing state on this file
                # so pause for now.
                self.stop()
            else:
                self.seek(self.state["current_pos"])
        if playing_state == PLAYER_PAUSE:
            self.pause()

    def set_source(self, source):
        self._source = source

    def play_webradio(self, webradio):
        self._change_file(webradio)

    def play_toggle(self):
        if self.get_state() == PLAYER_STOP:
            f = self._playing_media or self._source.get_current()
            self._change_file(f)
        elif self.get_state() in (PLAYER_PAUSE, PLAYER_PLAY):
            self.pause()

    def play(self):
        raise NotImplementedError

    def pause(self):
        raise NotImplementedError

    def on_media_stopped(self):
        if self._playing_media is not None:
            self._playing_media.stopped(self.get_position())

    def stop(self):
        if self.get_state() != PLAYER_STOP:
            self.on_media_stopped()
            self._source.queue_reset()
            self._change_file(None)

    def next(self):
        if self.get_state() != PLAYER_STOP:
            self._playing_media.skip()
        self.on_media_stopped()
        self._change_file(self._source.next())

    def previous(self):
        self.on_media_stopped()
        self._change_file(self._source.previous())

    def go_to(self, nb, type='id', source=None):
        self.on_media_stopped()
        self._change_file(self._source.go_to(nb, type, source))

    def get_volume(self):
        return self.__volume[self.__get_vol_type()]

    def set_volume(self, vol, relative=False, sig=True):
        if relative:
            vol = self.get_volume() + vol
        vol = min(max(0, vol), 100)
        self.__volume[self.__get_vol_type()] = vol

        # replaygain support
        if self._replaygain and self._playing_media is not None:
            try:
                scale = self._playing_media.replay_gain(
                    self._replaygain_opts["profiles"],
                    self._replaygain_opts["preamp_gain"],
                    self._replaygain_opts["fallback_gain"])
            except AttributeError:
                pass  # replaygain not supported
            else:
                vol = min(100.0, max(0.0, float(vol) * scale))

        # specific player implementation
        self._set_volume(vol, sig)
        if sig:
            self.dispatch_signame('player.status')
            self.osd("Volume: %d" % self.get_volume())

    def _set_volume(self, v, sig=True):
        raise NotImplementedError

    def __get_vol_type(self):
        if self._playing_media is None:
            mediatype_by_source = {
                "audiopls": "song",
                "audioqueue": "song",
                "videopls": "video",
                "webradio": "webradio"
            }
            return mediatype_by_source[self._source.get_current_sourcename()]
        else:
            return self._playing_media['type']

    def get_position(self):
        raise NotImplementedError

    def seek(self, pos, relative=False):
        if self.get_state() != PLAYER_STOP and self._playing_media.is_seekable():
            if relative:
                pos = int(pos) + self.get_position()
            self._set_position(pos)
            self.dispatch_signame('player.status')

    def _set_position(self, pos):
        raise NotImplementedError

    def get_state(self):
        raise NotImplementedError

    def get_available_video_options(self):
        return dict([(opt, opt in self.supported_options)
                     for opt in self.options])

    def set_video_option(self, name, value):
        if name not in self.supported_options:
            raise PlayerError(_("Video option %s is not supported "
                                "by %s player") % (name, self.NAME))

        if self._playing_media is not None and self._playing_media.has_video():
            func = {
                "current-audio": self.set_current_audio,
                "current-sub": self.set_current_sub,
                "av-offset": self.set_avoffset,
                "sub-offset": self.set_suboffset,
                "zoom": self.set_zoom,
                "aspect-ratio": self.set_aspectratio,
            }[name]
            if name not in ("aspect-ratio",):
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    raise PlayerError(_("Value %s not allowed "
                                        "for this option") % str(value))

            func(value)
            self._playing_media.playing_state[name] = value
            self.dispatch_signame('player.current')

    def set_zoom(self, zoom):
        self._player_set_zoom(zoom)
        self.osd(_("Zoom: %s") % zoom)

    def set_aspectratio(self, aspect):
        if aspect not in self.aspect_ratios:
            raise PlayerError(_("Video aspect ratio %s is not known") % aspect)

        self._player_set_aspectratio(aspect)
        self.osd(_("Video aspect ratio: %s") % aspect)

    def set_avoffset(self, offset):
        self._player_set_avoffset(offset)
        self.osd(_("Audio/Video offset: %d ms") % offset)

    def set_suboffset(self, offset):
        if self._playing_media.has_subtitle():
            self._player_set_suboffset(offset)
            self.osd(_("Subtitle offset: %d ms") % offset)

    def set_current_audio(self, idx):
        try:
            track = self._playing_media.audio_channels[idx]
        except KeyError:
            raise PlayerError(_("Current media hasn't multiple audio channel"))
        self._player_set_alang(track.ix)
        self.osd(_("Audio channel: %s") % track.language)

    def set_current_sub(self, idx):
        try:
            track = self._playing_media.subtitle_channels[idx]
        except KeyError:
            raise PlayerError(_("Current media hasn't multiple audio channel"))
        self._player_set_slang(track.ix)
        self.osd(_("Subtitle channel: %s") % track.language)

    def osd(self, text):
        if self._video_options["osd"] and self.is_playing() \
                and self._playing_media.has_video():
            self._osd_set(text)

    def _osd_set(self, text):
        raise NotImplementedError

    def get_playing(self):
        if self.is_playing():
            return self._playing_media
        return None

    def is_playing(self):
        return self.get_state() != PLAYER_STOP

    def get_status(self):
        status = [("state", self.get_state()), ("volume", self.get_volume())]

        if self._playing_media is not None:
            if not self._playing_media.is_seekable():
                status.append(("current", "%d:%d:%s" % (-1, -1, "webradio")))
            else:
                status.append(
                    ("current", "%d:%s:%s" % (self._playing_media["pos"],
                                              self._playing_media["id"],
                                              self._playing_media["source"])))

            if self.get_state() != PLAYER_STOP:
                position = self.get_position()
                if not self._playing_media.is_seekable():
                    length = position
                else:
                    length = self._playing_media["length"]
                status.append(("time", "%d:%d" % (position, length)))
        return dict(status)

    def close(self):
        # save state
        current = self._playing_media or {"pos": "-1", "source": "none"}
        self.state.update({
            "volume": self.__volume,
            "current": current["pos"],
            "current_source": current["source"],
            "current_pos": self.get_position(),
            "state": self.get_state()
        })
        # stop player if necessary
        if self.get_state() != PLAYER_STOP:
            self.stop()
        self.save_state()