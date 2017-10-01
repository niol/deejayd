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

from deejayd.common.component import SignalingComponent
from deejayd.common.component import PersistentStateComponent
from deejayd.ui import log
from deejayd.sources.audio import AudioSource
from deejayd.sources.video import VideoSource
from deejayd.sources.queue import QueueSource
from deejayd import DeejaydError


class SourceFactory(SignalingComponent, PersistentStateComponent):
    state_name = "source_state"
    initial_state = {"active": "audiopls"}

    def __init__(self, player, audio_library, video_library, config):
        super(SourceFactory, self).__init__()
        self.load_state()

        self.sources = {
           "audiopls": AudioSource(audio_library),
           "audioqueue": QueueSource(audio_library)
        }
        # Video
        if config.getboolean("video", "enabled"):
            self.sources["videopls"] = VideoSource(video_library)
        else:
            log.msg(_("Video support disabled"))

        if self.state["active"] not in self.sources:
            self.state["active"] = self.sources["audiopls"]
        player.set_source(self)
        player.load_state()

    def get_source(self, s):
        if s not in self.sources:
            raise DeejaydError(_("Source %s not found") % s)
        return self.sources[s]

    def set_source(self, s):
        if s not in self.sources:
            raise DeejaydError(_("Source %s not found") % s)
        self.state["active"] = s

    def close(self):
        self.save_state()
        for s in self.sources:
            self.sources[s].close()

    #
    # Functions called from the player
    #
    def get_current_sourcename(self):
        return self.state['active']

    def go_to(self, item_id, id_type="id", source_name=None):
        if source_name is not None:
            self.state["active"] = source_name
        return self.sources[self.state["active"]].go_to(item_id, id_type)

    def get_current(self):
        queue_media = self.sources["audioqueue"].get_current() or \
                      self.sources["audioqueue"].next()
        if queue_media:
            return queue_media

        return self.sources[self.state["active"]].get_current() or \
            self.sources[self.state["active"]].next(explicit=False)

    def next(self, explicit=True):
        queue_media = self.sources["audioqueue"].next(explicit)
        return queue_media or self.sources[self.state["active"]].next(explicit)

    def previous(self):
        return self.sources[self.state["active"]].previous()

    def queue_reset(self):
        self.sources["audioqueue"].reset()


def init(player, a_library, v_library, config):
    return SourceFactory(player, a_library, v_library, config)
