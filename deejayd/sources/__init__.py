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

from deejayd.component import SignalingComponent, PersistentStateComponent
from deejayd.ui import log
from deejayd.player import PlayerError
from deejayd.sources._base import SourceError

class UnknownSourceException: pass

class SourceFactory(SignalingComponent, PersistentStateComponent):
    sources_list = ("playlist", "queue", "webradio", "video", "panel")
    state_name = "source_state"
    initial_state = {"current": "playlist"}

    def __init__(self, player, audio_library, video_library, plg_mnt, config):
        super(SourceFactory, self).__init__()
        self.load_state()
        activated_sources = config.getlist('general', "activated_modes")

        self.sources_obj = {}
        from deejayd.sources import queue
        self.sources_obj["queue"] = queue.QueueSource(audio_library)
        # playlist
        if "playlist" in activated_sources:
            from deejayd.sources import playlist
            self.sources_obj["playlist"] = playlist.PlaylistSource(audio_library)
        else:
            log.info(_("Playlist support disabled"))

        # panel
        if "panel" in activated_sources:
            from deejayd.sources import panel
            self.sources_obj["panel"] = panel.PanelSource(audio_library, config)
        else:
            log.info(_("Panel support disabled"))

        # Webradio
        if "webradio" in activated_sources and player.is_supported_uri("http"):
            from deejayd.sources import webradio
            self.sources_obj["webradio"] = webradio.WebradioSource()
        else:
            log.info(_("Webradio support disabled"))

        # Video
        if "video" in activated_sources:
            from deejayd.sources import video
            self.sources_obj["video"] = video.VideoSource(video_library)
        else:
            log.info(_("Video support disabled"))

        # restore recorded source
        source = self.state["current"]
        try: self.set_source(source)
        except UnknownSourceException:
            log.err(_("Unable to set recorded source %s") % str(source))
            self.set_source(self.get_available_sources()[0])

        player.set_source(self)
        player.load_state()

    def set_option(self, source, name, value):
        try: self.sources_obj[source].set_option(name, value)
        except KeyError:
            raise UnknownSourceException
        except NotImplementedError:
            raise SourceError(_("option %s not supported for this mode"))
        self.dispatch_signame('player.status')

    def get_current_sourcename(self):
        return self.state['current']

    def get_source(self, s):
        if s not in self.sources_obj.keys():
            raise UnknownSourceException

        return self.sources_obj[s]

    def set_source(self, s):
        if s not in self.sources_obj.keys():
            raise UnknownSourceException

        self.state["current"] = s
        self.dispatch_signame('mode')
        return True

    def get_status(self):
        status = [("mode", self.state["current"])]
        for k in self.sources_obj.keys():
            status.extend(self.sources_obj[k].get_status())
        return status

    def get_all_sources(self):
        return [m for m in self.sources_list if m != "queue"]

    def get_available_sources(self):
        modes = self.sources_obj.keys()
        modes.remove("queue")
        return modes

    def is_available(self, mode):
        return mode in self.sources_obj.keys()

    def close(self):
        super(SourceFactory, self).close()
        for k in self.sources_obj.keys():
            self.sources_obj[k].close()

    #
    # Functions called from the player
    #
    def get(self, nb=None, type="id", source_name=None):
        src = source_name or self.state["current"]
        return self.sources_obj[src].go_to(nb, type)

    def get_current(self):
        queue_media = self.sources_obj["queue"].get_current() or \
                      self.sources_obj["queue"].next()
        if queue_media:
            return queue_media

        current = self.sources_obj[self.state["current"]].get_current() or \
            self.sources_obj[self.state["current"]].next(explicit=False)
        return current

    def next(self, explicit=True):
        queue_media = self.sources_obj["queue"].next(explicit)
        if queue_media:
            return queue_media
        return self.sources_obj[self.state["current"]].next(explicit)

    def previous(self):
        return self.sources_obj[self.state["current"]].previous()

    def queue_reset(self):
        self.sources_obj["queue"].reset()


def init(player, audio_library, video_library, pl_mngt, config):
    source = SourceFactory(player, audio_library, video_library, pl_mngt, config)
    return source


# vim: ts=4 sw=4 expandtab
