# Deejayd, a media player daemon
# Copyright (C) 2007 Mickael Royer <mickael.royer@gmail.com>
#                    Alexandre Rossi <alexandre.rossi@gmail.com>
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
from deejayd.ui import log
from deejayd.player import PlayerError

class UnknownSourceException: pass

class SourceFactory:
    sources_list = ("playlist","queue","webradio","video","dvd")

    def __init__(self,player,db,audio_library,video_library,config):
        self.sources_obj = {}
        self.current = ""
        self.db = db
        video_support = config.getboolean('general', 'video_support')

        # Playlist and Queue
        from deejayd.sources import playlist, queue
        self.sources_obj["playlist"] = playlist.PlaylistSource(db,audio_library)
        self.sources_obj["queue"] = queue.QueueSource(db,\
            audio_library,video_library)

        # Webradio
        if player.is_supported_uri("http"):
            from deejayd.sources import webradio
            self.sources_obj["webradio"] = webradio.WebradioSource(db)
        else: log.info(_("Webradio support disabled for the choosen backend"))

        # Video
        if video_library:
            from deejayd.sources import video
            try: player.init_video_support()
            except PlayerError:
                # Critical error, we have to quit deejayd
                msg = _('Cannot initialise video support, either disable video support or check your player video support.')
                log.err(msg)
                sys.exit(msg)
            self.sources_obj["video"] = video.VideoSource(db, video_library)

        # dvd
        if video_support and player.is_supported_uri("dvd"):
            from deejayd.sources import dvd
            try: self.sources_obj["dvd"] = dvd.DvdSource(player,db,config)
            except dvd.DvdError:
                log.err(_("Unable to init dvd support"))
        else: log.info(_("DVD support is disabled"))

        # restore recorded source
        source = db.get_state("source")
        try: self.set_source(source)
        except UnknownSourceException:
            log.err(_("Unable to set recorded source %s") % str(source))
            self.set_source("playlist")

        player.set_source(self)
        player.load_state()

    def get_source(self,s):
        if s not in self.sources_obj.keys():
            raise UnknownSourceException

        return self.sources_obj[s]

    def set_source(self,s):
        if s not in self.sources_obj.keys():
            raise UnknownSourceException

        self.current = s
        return True

    def get_status(self):
        status = [("mode",self.current)]
        for k in self.sources_obj.keys():
            status.extend(self.sources_obj[k].get_status())

        return status

    def get_available_sources(self):
        modes = self.sources_obj.keys()
        modes.remove("queue")
        return modes

    def close(self):
        self.db.set_state([(self.current,"source")])
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

    def next(self, random,repeat):
        return self.sources_obj["queue"].next(random,repeat) or \
               self.sources_obj[self.current].next(random,repeat)

    def previous(self,random,repeat):
        return self.sources_obj[self.current].previous(random,repeat)

    def queue_reset(self):
        self.sources_obj["queue"].reset()


def init(player,db,audio_library,video_library,config):
    source = SourceFactory(player,db,audio_library,video_library,config)
    return source


# vim: ts=4 sw=4 expandtab
