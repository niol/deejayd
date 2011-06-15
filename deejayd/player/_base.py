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

import cPickle as pickle

from deejayd.component import SignalingComponent, JSONRpcComponent
from deejayd.plugins import PluginError, IPlayerPlugin
from deejayd.player import PlayerError
from deejayd.ui import log
from deejayd.utils import get_uris_from_pls


__all__ = ['PLAYER_PLAY', 'PLAYER_PAUSE', 'PLAYER_STOP', '_BasePlayer']

PLAYER_PLAY = "play"
PLAYER_PAUSE = "pause"
PLAYER_STOP = "stop"

class _BasePlayer(SignalingComponent, JSONRpcComponent):
    VIDEO_SUPPORT = False

    def __init__(self, db, plugin_manager, config):
        super(_BasePlayer, self).__init__()
        self.config = config
        self.db = db
        # Init plugins
        self.plugins = []
        plugins_cls = plugin_manager.get_plugins(IPlayerPlugin)
        for plugin in plugins_cls:
            try: self.plugins.append(plugin(config))
            except PluginError, err:
                log.err(_("Unable to init %s plugin: %s")%(plugin.NAME, err))

        # Initialise var
        self._video_support = False
        self._source = None
        self._media_file = None
        self._replaygain = config.getboolean("general","replaygain")
        self.__volume = {"song": 100, "video": 100, "webradio": 100}

    def load_state(self):
        # Restore volume
        recorded_volume = self.db.get_state("volume")
        try:
            self.__volume = pickle.loads(recorded_volume.encode("utf-8"))
        except pickle.UnpicklingError: # old record
            self.__volume["song"] = int(recorded_volume)

        # Restore current media
        media_pos = int(self.db.get_state("current"))
        source = self.db.get_state("current_source")
        if media_pos != -1 and source not in ("queue", "none", 'webradio'):
            self._media_file = self._source.get(media_pos, "pos", source)

        # Update state
        state = self.db.get_state("state")
        if state != PLAYER_STOP and source != 'webradio':
            try:
                self.play()
            except PlayerError:
                # There is an issue restoring the playing state on this file
                # so pause for now.
                self.stop()
            else:
                if self._media_file and self._media_file["source"] != "queue":
                    self.seek(int(self.db.get_state("current_pos")))
        if state == PLAYER_PAUSE:
            self.pause()

    def set_source(self, source):
        self._source = source

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
                if not len(urls): # we don't succeed to extract uri
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
        raise NotImplementedError

    def next(self):
        if self.get_state() != PLAYER_STOP:
            try: self._media_file.skip()
            except AttributeError: pass
        self._change_file(self._source.next())

    def previous(self):
        self._change_file(self._source.previous())

    def go_to(self, nb, type = 'id', source = None):
        self._change_file(self._source.get(nb, type, source))

    def get_volume(self):
        return self.__volume[self.__get_vol_type()]

    def set_volume(self, v, sig = True):
        new_volume = min(100, int(v))
        type = self.__get_vol_type()
        self.__volume[type] = new_volume

        # replaygain support
        vol = self.__volume[type]
        if self._replaygain and self._media_file is not None:
            try: scale = self._media_file.replay_gain()
            except AttributeError: pass # replaygain not supported
            else:
                vol = max(0.0, min(4.0, float(vol)/100.0 * scale))
                vol = min(100, int(vol * 100))

        # specific player implementation
        self._set_volume(vol, sig)

    def _set_volume(self, v, sig = True):
        raise NotImplementedError

    def __get_vol_type(self):
        if self._media_file is None:
            mediatype_by_source = {
                    "playlist": "song",
                    "panel": "song",
                    "video": "video",
                    "dvd": "video",
                    "webradio": "webradio"
                }
            return mediatype_by_source[self._source.current]
        else:
            return self._media_file['type']

    def get_position(self):
        raise NotImplementedError

    def seek(self, pos, relative = False):
        if relative and self.get_state()!="stop"\
                and self._media_file["type"]!="webradio":
            cur_pos = self.get_position()
            pos = int(pos) + cur_pos
        self._set_position(pos)

    def _set_position(self, pos):
        raise NotImplementedError

    def get_state(self):
        raise NotImplementedError

    def set_video_option(self, name, value):
        if not self._media_file or self._media_file["type"] != "video" or\
                                   self.get_state() == PLAYER_STOP:
            return

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

        try: options[name](value)
        except KeyError:
            raise PlayerError(_("Video option %s is not known") % name)

    def set_zoom(self, zoom):
        raise NotImplementedError

    def set_avoffset(self, offset):
        raise NotImplementedError

    def set_suboffset(self, offset):
        raise NotImplementedError

    def set_aspectratio(self, aspect):
        raise NotImplementedError

    def set_alang(self,lang_idx):
        try: audio_tracks = self._media_file["audio"]
        except KeyError:
            raise PlayerError(_("Current media hasn't multiple audio channel"))
        else:
            if lang_idx in (-2,-1): # disable/auto audio channel
                self._player_set_alang(lang_idx)
                self._media_file["audio_idx"] = self._player_get_alang()
                return
            found = False
            for track in audio_tracks:
                if track['ix'] == lang_idx: # audio track exists
                    self._player_set_alang(lang_idx)
                    found = True
                    break
            if not found:
                raise PlayerError(_("Audio channel %d not found") % lang_idx)
            self._media_file["audio_idx"] = self._player_get_alang()

    def set_slang(self,lang_idx):
        try: sub_tracks = self._media_file["subtitle"]
        except KeyError:
            raise PlayerError(_("Current media hasn't multiple sub channel"))
        else:
            if lang_idx in (-2,-1): # disable/auto subtitle channel
                self._player_set_slang(lang_idx)
                self._media_file["subtitle_idx"] = self._player_get_slang()
                return
            found = False
            for track in sub_tracks:
                if track['ix'] == lang_idx: # audio track exists
                    self._player_set_slang(lang_idx)
                    found = True
                    break
            if not found:
                raise PlayerError(_("Sub channel %d not found") % lang_idx)
            self._media_file["subtitle_idx"] = self._player_get_slang()

    def get_playing(self):
        if self.is_playing():
            return self._media_file
        raise PlayerError(_("No media file is currently playing"))

    def is_playing(self):
        return self.get_state() != PLAYER_STOP

    def get_status(self):
        status = [("state",self.get_state()),("volume",self.get_volume())]

        if self._media_file:
            status.append(("current",\
              "%d:%s:%s" % (self._media_file["pos"],\
                    str(self._media_file["id"]), self._media_file["source"])))

        if self.get_state() != PLAYER_STOP:
            position = self.get_position()
            if "length" not in self._media_file.keys() or \
                                              self._media_file["length"] == 0:
                length = position
            else:
                length = int(self._media_file["length"])
            status.extend([ ("time","%d:%d" % (position, length)) ])

        return status

    def close(self):
        # close plugins
        for plugin in self.plugins:
            plugin.close()

        # save state
        current = self._media_file or {"pos": "-1", "source": "none"}
        states = [
            (pickle.dumps(self.__volume), "volume"),
            (current["pos"], "current"),
            (current["source"], "current_source"),
            (str(self.get_position()), "current_pos"),
            (self.get_state(), "state"),
            ]
        self.db.set_state(states)

        # stop player if necessary
        if self.get_state() != PLAYER_STOP:
            self.stop()

# vim: ts=4 sw=4 expandtab
