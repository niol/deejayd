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

from deejayd.common.component import SignalingComponent, PersistentStateComponent
from deejayd.ui import log
from deejayd.sources._base import SourceError
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

        # restore recorded source
        if 'active' not in self.state\
        or self.state["active"] not in self.sources:
            self.state["active"] = self.sources.keys()[0]

        player.set_source(self)
        player.load_state()

    def get_source(self, s):
        if s not in self.sources.keys():
            raise DeejaydError(_("Source %s not found") % s)

        return self.sources[s]

    def set_source(self, s):
        if s not in self.sources.keys():
            raise DeejaydError(_("Source %s not found") % s)

        self.state["active"] = s
        return True

    def close(self):
        super(SourceFactory, self).close()
        for s in self.sources.values():
            s.close()

    #
    # Functions called from the player
    #
    def get_current_sourcename(self):
        return self.state['active']

    def go_to(self, id, type="id", source_name=None):
        if source_name is not None:
            self.state["active"] = source_name
        return self.sources[self.state["active"]].go_to(id, type)

    def get_current(self):
        queue_media = self.sources["audioqueue"].get_current() or \
                      self.sources["audioqueue"].next()
        if queue_media:
            return queue_media

        current = self.sources[self.state["active"]].get_current() or \
            self.sources[self.state["active"]].next(explicit=False)
        return current

    def next(self, explicit=True):
        queue_media = self.sources["audioqueue"].next(explicit)
        if queue_media:
            return queue_media
        return self.sources[self.state["active"]].next(explicit)

    def previous(self):
        return self.sources[self.state["active"]].previous()

    def queue_reset(self):
        self.sources["audioqueue"].reset()


def init(player, audio_library, video_library, config):
    source = SourceFactory(player, audio_library, video_library, config)
    return source


# vim: ts=4 sw=4 expandtab
