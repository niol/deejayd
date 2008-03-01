# Deejayd, a media player daemon
# Copyright (C) 2007-2008 Mickael Royer <mickael.royer@gmail.com>
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

import sys

from deejayd.component import SignalingComponent
from deejayd.ui import log
from deejayd.player import PlayerError

class UnknownSourceException: pass

class SourceFactory(SignalingComponent):
    sources_list = ("playlist","queue","webradio","video","dvd")

    def __init__(self,player,db,audio_library,video_library,config):
        SignalingComponent.__init__(self)
        self.sources_obj = {}
        self.current = ""
        self.db = db
        activated_sources = config.get('general', "activated_modes").split(",")

        from deejayd.sources import queue
        self.sources_obj["queue"] = queue.QueueSource(db,\
            audio_library,video_library)
        # playlist
        if "playlist" in activated_sources:
            from deejayd.sources import playlist
            self.sources_obj["playlist"] = playlist.PlaylistSource(db,\
                                                                 audio_library)
        else:
            log.info(_("Playlist support disabled"))

        # Webradio
        if "webradio" in activated_sources and player.is_supported_uri("http"):
            from deejayd.sources import webradio
            self.sources_obj["webradio"] = webradio.WebradioSource(db)
        else:
            log.info(_("Webradio support disabled"))

        # init video support in player
        if "video" in activated_sources or "dvd" in activated_sources:
            try: player.init_video_support()
            except PlayerError:
                # Critical error, we have to quit deejayd
                msg = _('Cannot initialise video support, either disable video and dvd mode or check your player video support.')
                log.err(msg)
                sys.exit(msg)

        # Video
        if "video" in activated_sources:
            from deejayd.sources import video
            self.sources_obj["video"] = video.VideoSource(db, video_library)
        else:
            log.info(_("Video support disabled"))

        # dvd
        if "dvd" in activated_sources and player.is_supported_uri("dvd"):
            from deejayd.sources import dvd
            try: self.sources_obj["dvd"] = dvd.DvdSource(player,db,config)
            except dvd.DvdError:
                log.err(_("Unable to init dvd support"))
        else:
            log.info(_("DVD support disabled"))

        # restore recorded source
        source = db.get_state("source")
        try: self.set_source(source)
        except UnknownSourceException:
            log.err(_("Unable to set recorded source %s") % str(source))
            self.set_source(self.get_available_sources()[0])

        # load random/repeat options state
        self.source_options = {}
        self.source_options["random"] = int(self.db.get_state("random"))
        self.source_options["repeat"] = int(self.db.get_state("repeat"))

        player.set_source(self)
        player.load_state()

    def set_option(self,name,value):
        if name not in self.source_options.keys(): raise KeyError
        self.source_options[name] = value
        self.dispatch_signame('player.status')

    def get_source(self,s):
        if s not in self.sources_obj.keys():
            raise UnknownSourceException

        return self.sources_obj[s]

    def set_source(self,s):
        if s not in self.sources_obj.keys():
            raise UnknownSourceException

        self.current = s
        self.dispatch_signame('mode')
        return True

    def get_status(self):
        status = [("mode",self.current)]
        for k in self.sources_obj.keys():
            status.extend(self.sources_obj[k].get_status())

        for key in self.source_options.keys():
            status.append((key,self.source_options[key]))

        return status

    def get_available_sources(self):
        modes = self.sources_obj.keys()
        modes.remove("queue")
        return modes

    def is_available(self, mode):
        return mode in self.sources_obj.keys()

    def close(self):
        states = [(self.current,"source")]
        for key in self.source_options:
            states.append((str(self.source_options[key]),key))
        self.db.set_state(states)

        for k in self.sources_obj.keys():
            self.sources_obj[k].close()

    #
    # Functions called from the player
    #
    def get(self, nb = None, type = "id", source_name = None):
        src = source_name or self.current
        return self.sources_obj[src].go_to(nb,type)

    def get_current(self):
        return self.sources_obj["queue"].get_current() or \
               self.sources_obj[self.current].get_current()

    def next(self):
        return self.sources_obj["queue"].next(0,0) or \
               self.sources_obj[self.current].next(\
                 self.source_options["random"],self.source_options["repeat"])

    def previous(self):
        return self.sources_obj[self.current].previous(\
            self.source_options["random"],self.source_options["repeat"])

    def queue_reset(self):
        self.sources_obj["queue"].reset()


def init(player,db,audio_library,video_library,config):
    source = SourceFactory(player,db,audio_library,video_library,config)
    return source


# vim: ts=4 sw=4 expandtab
