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

from deejayd.component import SignalingComponent, JSONRpcComponent
from deejayd.component import PersistentStateComponent
from deejayd.plugins import PluginError, IPlayerPlugin
from deejayd.player import PlayerError
from deejayd.ui import log
from deejayd.utils import get_uris_from_pls


__all__ = ['PLAYER_PLAY', 'PLAYER_PAUSE', 'PLAYER_STOP', '_BasePlayer']

PLAYER_PLAY = "play"
PLAYER_PAUSE = "pause"
PLAYER_STOP = "stop"

class _BasePlayer(SignalingComponent, JSONRpcComponent, \
                  PersistentStateComponent):
    state_name = "player"
    # initial value for player state
    initial_state = {
        "volume": {"song": 100, "video": 100, "webradio": 100},
        "state": "stop",
        "current":-1,
        "current_source": "none",
        "current_pos": 0,
    }
    options = (\
            "audio_lang",
            "sub_lang",
            "av_offset",
            "sub_offset",
            "zoom",
            "aspect_ratio"\
        )
    supported_options = []
    default_channels = []

    def __init__(self, plugin_manager, config):
        super(_BasePlayer, self).__init__()
        self.config = config
        # Init plugins
        self.plugins = []
        plugins_cls = plugin_manager.get_plugins(IPlayerPlugin)
        for plugin in plugins_cls:
            try: self.plugins.append(plugin(config))
            except PluginError, err:
                log.err(_("Unable to init %s plugin: %s") % (plugin.NAME, err))

        # Initialise var
        self._source = None
        self._media_file = None
        self._replaygain = config.getboolean("general", "replaygain")

        # get video options
        self._video_options = {
                "display": self.config.get("video", "display"),
                "fullscreen": self.config.getboolean("video", "fullscreen"),
                "osd": self.config.getboolean("video", "osd_support"),
                "osd_size": self.config.getint("video", "osd_font_size"),
            }
        self._aspect_ratios = ("auto", "1:1", "4:3", "16:9")
        self._default_aspect_ratio = "auto"

    def load_state(self):
        super(_BasePlayer, self).load_state()
        # Restore volume
        self.__volume = self.state["volume"]

        # Restore current media
        media_pos = int(self.state["current"])
        source = self.state["current_source"]
        if media_pos != -1 and source not in ("queue", "none", 'webradio'):
            self._media_file = self._source.go_to(media_pos, "pos", source)

        # Update playing state
        playing_state = self.state["state"]
        if playing_state != PLAYER_STOP and self._media_file is not None:
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
            file = self._media_file or self._source.get_current()
            self._change_file(file)
        elif self.get_state() in (PLAYER_PAUSE, PLAYER_PLAY):
            self.pause()

    def play(self):
        if not self._media_file: return
        if self._media_file["type"] == "webradio":
            if self._media_file["url-type"] == "pls":
                try:
                    urls = get_uris_from_pls(self._media_file["url"])
                except IOError:
                    raise PlayerError(_("Unable to get pls for webradio %s")\
                                      % self._media_file["title"])
                if not len(urls):  # we don't succeed to extract uri
                    raise PlayerError(\
                            _("Unable to extract uri from pls playlist"))
                self._media_file.update({"urls": urls, "url-index": 0, \
                                         "url-type": "urls"})
            idx = self._media_file["url-index"]
            self._media_file["uri"] = \
                    self._media_file["urls"][idx].encode("utf-8")

    def pause(self):
        raise NotImplementedError

    def stop(self):
        if self.get_state() != PLAYER_STOP:
            self._source.queue_reset()
            self._change_file(None)
            self.dispatch_signame('player.status')

    def next(self):
        if self.get_state() != PLAYER_STOP:
            try: self._media_file.skip()
            except AttributeError: pass
        self._change_file(self._source.next())

    def previous(self):
        self._change_file(self._source.previous())

    def go_to(self, nb, type='id', source=None):
        self._change_file(self._source.go_to(nb, type, source))

    def get_volume(self):
        return self.__volume[self.__get_vol_type()]

    def set_volume(self, v, sig=True):
        if int(v) not in range(0, 101):
            raise PlayerError(_("Volume value has to be between 0 and 100"))
        new_volume = min(100, int(v))
        type = self.__get_vol_type()
        self.__volume[type] = new_volume

        # replaygain support
        vol = self.__volume[type]
        if self._replaygain and self._media_file is not None:
            try: scale = self._media_file.replay_gain()
            except AttributeError: pass  # replaygain not supported
            else:
                vol = max(0.0, min(4.0, float(vol) / 100.0 * scale))
                vol = min(100, int(vol * 100))

        # specific player implementation
        self._set_volume(vol, sig)
        if sig:
            self.dispatch_signame('player.status')
            self.osd("Volume: %d" % self.get_volume())

    def set_volume_relative(self, step):
        new_vol = self.get_volume() + step
        self.set_volume(min(max(0, new_vol), 100))

    def _set_volume(self, v, sig=True):
        raise NotImplementedError

    def __get_vol_type(self):
        if self._media_file is None:
            mediatype_by_source = {
                    "audiopls": "song",
                    "audioqueue": "song",
                    "videopls": "video",
                    "webradio": "webradio"
                }
            return mediatype_by_source[self._source.get_current_sourcename()]
        else:
            return self._media_file['type']

    def get_position(self):
        raise NotImplementedError

    def seek(self, pos, relative=False):
        if relative and self.get_state() != "stop"\
                and self._media_file["type"] != "webradio":
            cur_pos = self.get_position()
            pos = int(pos) + cur_pos
        self._set_position(pos)
        self.dispatch_signame('player.status')

    def _set_position(self, pos):
        raise NotImplementedError

    def get_state(self):
        raise NotImplementedError

    def get_available_video_options(self):
        ans = {}
        for opt in self.options:
            ans[opt] = opt in self.supported_options
        return ans

    def set_video_option(self, name, value):
        if name not in self.options:
            raise PlayerError(_("Video option %s is not known") % name)
        elif name not in self.supported_options:
            raise PlayerError(_(\
                        "Video option %s is not supported by %s player")\
                               % (name, self.NAME))

        options = {
            "audio_lang": self.set_alang,
            "sub_lang": self.set_slang,
            "av_offset": self.set_avoffset,
            "sub_offset": self.set_suboffset,
            "zoom": self.set_zoom,
            "aspect_ratio": self.set_aspectratio,
            }
        if name not in ("aspect_ratio",):
            try: value = int(value)
            except (ValueError, TypeError):
                raise PlayerError(_("Value %s not allowed for this option")\
                        % str(value))

        if not self._current_is_video():
            return
        options[name](value)
        self.dispatch_signame('player.current')

    def set_zoom(self, zoom):
        raise NotImplementedError

    def set_aspectratio(self, aspect):
        if aspect not in self._aspect_ratios:
            raise PlayerError(_("Video aspect ration %s is not known.") % aspect)
        self._default_aspect_ratio = aspect
        if self._current_is_video():
            self._player_set_aspectratio(aspect)
            self._media_file["aspect_ratio"] = self._default_aspect_ratio

    def set_avoffset(self, offset):
        if self._current_is_video():
            self._player_set_avoffset(offset)
            self._media_file["av_offset"] = offset
            self.osd(_("Audio/Video offset: %d ms") % offset)

    def set_suboffset(self, offset):
        if "subtitle" in self._media_file.keys():
            self._player_set_suboffset(offset)
            self._media_file["sub_offset"] = offset
            self.osd(_("Subtitle offset: %d ms") % offset)

    def set_alang(self, lang_idx):
        try: audio_tracks = self._media_file["audio"]
        except KeyError:
            raise PlayerError(_("Current media hasn't multiple audio channel"))
        else:
            if lang_idx in (-2, -1):  # disable/auto audio channel
                self._player_set_alang(lang_idx)
                self._media_file["audio_idx"] = self._player_get_alang()
                return
            found = False
            for track in audio_tracks:
                if track['ix'] == lang_idx:  # audio track exists
                    self._player_set_alang(lang_idx)
                    found = True
                    break
            if not found:
                raise PlayerError(_("Audio channel %d not found") % lang_idx)
            self._media_file["audio_idx"] = self._player_get_alang()

    def set_slang(self, lang_idx):
        try: sub_tracks = self._media_file["subtitle"]
        except KeyError:
            raise PlayerError(_("Current media hasn't multiple sub channel"))
        else:
            if lang_idx in (-2, -1):  # disable/auto subtitle channel
                self._player_set_slang(lang_idx)
                self._media_file["subtitle_idx"] = self._player_get_slang()
                return
            found = False
            for track in sub_tracks:
                if track['ix'] == lang_idx:  # audio track exists
                    self._player_set_slang(lang_idx)
                    found = True
                    break
            if not found:
                raise PlayerError(_("Sub channel %d not found") % lang_idx)
            self._media_file["subtitle_idx"] = self._player_get_slang()

    def osd(self, text):
        if self._video_options["osd"] and self._current_is_video():
            self._osd_set(text)

    def _osd_set(self, text):
        raise NotImplementedError

    def get_playing(self):
        if self.is_playing():
            return self._media_file
        return None

    def is_playing(self):
        return self.get_state() != PLAYER_STOP

    def get_status(self):
        status = [("state", self.get_state()), ("volume", self.get_volume())]

        if self._media_file:
            if self._media_file["type"] == "webradio":
                status.append(("current", "%d:%d:%s" % (-1 , -1, "webradio")))
            else:
                status.append(("current", \
                  "%d:%s:%s" % (self._media_file["pos"], \
                        str(self._media_file["id"]), self._media_file["source"])))

            if self.get_state() != PLAYER_STOP:
                position = self.get_position()
                if "length" not in self._media_file.keys() or \
                                              self._media_file["length"] == 0:
                    length = position
                else:
                    length = int(self._media_file["length"])
                status.extend([ ("time", "%d:%d" % (position, length)) ])

        return status

    def close(self):
        # close plugins
        for plugin in self.plugins:
            plugin.close()

        # save state
        current = self._media_file or {"pos": "-1", "source": "none"}
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
        super(_BasePlayer, self).close()

    def _current_is_video(self):
        return self._media_file is not None \
                and self._media_file['type'] == 'video'

    def _has_external_subtitle(self, media=None):
        media_file = media or self._media_file
        return media_file is not None \
            and "external_subtitle" in media_file \
            and media_file["external_subtitle"].startswith("file://")

    def _init_video_information(self):
        if self._current_is_video():
            # subtitles
            if self._has_external_subtitle():
                self._media_file["subtitle"] = list(self.default_channels) + \
                                               [{"lang": "external", "ix":1}]
            elif "subtitle_channels" in self._media_file.keys() and\
                    int(self._media_file["subtitle_channels"]) > 0:
                self._media_file["subtitle"] = list(self.default_channels)
                for i in range(int(self._media_file["subtitle_channels"])):
                    self._media_file["subtitle"].append(\
                        {"lang": _("Sub channel %d") % (i + 1,), "ix": i})

            # audio channels
            if "audio_channels" in self._media_file.keys() and \
                    int(self._media_file["audio_channels"]) > 1:
                audio_channels = list(self.default_channels)
                for i in range(int(self._media_file["audio_channels"])):
                    audio_channels.append(\
                            {"lang": _("Audio channel %d") % (i + 1,), "ix": i})
                self._media_file["audio"] = audio_channels

            self._media_file["av_offset"] = 0
            self._media_file["zoom"] = 100

            if "audio" in self._media_file:
                self._media_file["audio_idx"] = self._player_get_alang()
            else:
                self._player_set_alang(-1)  # auto audio channel
            if "subtitle" in self._media_file:
                self._media_file["sub_offset"] = 0
                self._media_file["subtitle_idx"] = self._player_get_slang()
            else:
                self._player_set_slang(-1)  # auto subtitle channel
                try: del self._media_file["sub_offset"]
                except KeyError: pass

            # set video aspect ration to default value
            try:
                self.set_video_option("aspect_ratio",
                                      self._default_aspect_ratio)
            except PlayerError:  # not supported by the player
                pass

# vim: ts=4 sw=4 expandtab
