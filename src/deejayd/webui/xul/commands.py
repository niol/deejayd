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

from deejayd.ui.config import DeejaydConfig
from deejayd.webui import commands as default_commands

class _DefaultAnswer(object):

    def set_answer(self):
        status = self._deejayd.get_status()
        # player update
        cur = None
        cur_list = self._deejayd.get_current().get_medias()
        if len(cur_list) == 1:
            cur = cur_list[0]
        self._answer.set_player(status, cur)

        # source update
        self._answer.set_mode(status, self._deejayd)

        # video library update
        stats = self._deejayd.get_stats()
        if "video" in status.keys() and "video_library_update" in stats.keys():
            self._answer.set_videodir(int(stats["video_library_update"]),\
                self._deejayd)

class Init(_DefaultAnswer, default_commands._Command):
    name = "init"

    def set_answer(self):
        status = self._deejayd.get_status()
        # available modes
        av_modes = self._deejayd.get_mode()
        self._answer.set_available_modes(av_modes)

        # current mode
        self._answer.set_view_mode(status["mode"])

        # config parms
        config = DeejaydConfig()
        refresh = config.get('webui','refresh')
        self._answer.set_config({"refresh": refresh})

        if "playlist" in status.keys():
            # audio files list
            files_list = self._deejayd.get_audio_dir("")
            self._answer.set_audiofile_list(files_list, "")

            # playlist list
            pls_list = self._deejayd.get_playlist_list()
            self._answer.set_playlist_list(pls_list.get_medias())

        if "panel" in status.keys(): # set panel
            self._answer.init_panel_tags(self._deejayd)
            self._answer.set_panel(self._deejayd)
        super(Init, self).set_answer()

class Refresh(_DefaultAnswer, default_commands._Command):
    name = "refresh"

class SetMode(_DefaultAnswer, default_commands.SetMode):

    def set_answer(self):
        self._answer.set_view_mode(self._args["mode"])
        super(SetMode, self).set_answer()

#
# Player controls
#
class PlayToggle(_DefaultAnswer, default_commands.PlayToggle): pass
class GoTo(_DefaultAnswer, default_commands.GoTo): pass
class Stop(_DefaultAnswer, default_commands.Stop): pass
class Next(_DefaultAnswer, default_commands.Next): pass
class Previous(_DefaultAnswer, default_commands.Previous): pass

class Repeat(_DefaultAnswer, default_commands._Command):
    name = "repeat"
    command_args = [{"name":"source","type":"enum_str","req":True,\
                     "values":("panel","playlist","video")}]

    def execute(self):
        status = self._deejayd.get_status()
        val = status[self._args["source"]+"repeat"] == 1 and (0,) or (1,)
        self._deejayd.set_option(self._args["source"],\
            "repeat",val[0]).get_contents()

class PlayOrder(_DefaultAnswer, default_commands.PlayOrder): pass
class Volume(_DefaultAnswer, default_commands.Volume): pass
class Seek(_DefaultAnswer, default_commands.Seek): pass
class PlayerOption(_DefaultAnswer, default_commands.PlayerOption): pass
class MediaRating(_DefaultAnswer, default_commands.MediaRating): pass

#
# Library commands
#
class AudioLibraryUpdate(default_commands._Command):
    name = "audioUpdate"

    def execute(self):
        rs = self._deejayd.update_audio_library()
        self._answer.set_update_library(rs["audio_updating_db"], "audio")

class VideoLibraryUpdate(default_commands._Command):
    name = "videoUpdate"

    def execute(self):
        rs = self._deejayd.update_video_library()
        self._answer.set_update_library(rs["video_updating_db"], "video")

class AudioUpdateCheck(default_commands._Command):
    name = "audio_update_check"
    command_args = [{"name": "id", "type": "int", "req": True}]

    def set_answer(self):
        status = self._deejayd.get_status()
        if "audio_updating_db" in status.keys() and \
                int(status["audio_updating_db"]) == int(self._args["id"]):
            self._answer.set_update_library(self._args["id"], "audio")
        else:
            self._answer.set_update_library(self._args["id"], "audio", "0")
            if "audio_updating_error" in status.keys():
                self._answer.set_error(status["audio_updating_error"])
            else:
                self._answer.set_msg(_("The audio library has been updated"))

                files_list = self._deejayd.get_audio_dir()
                self._answer.set_audiofile_list(files_list, "")

class VideoUpdateCheck(default_commands._Command):
    name = "video_update_check"
    command_args = [{"name": "id", "type": "int", "req": True}]

    def set_answer(self):
        status = self._deejayd.get_status()
        if "video_updating_db" in status.keys() and \
                int(status["video_updating_db"]) == int(self._args["id"]):
            self._answer.set_update_library(self._args["id"], "video")
        else:
            self._answer.set_update_library(self._args["id"], "video", "0")
            if "video_updating_error" in status.keys():
                self._answer.set_error(status["video_updating_error"])
            else:
                self._answer.set_msg(_("The video library has been updated"))

                stats = self._deejayd.get_stats()
                self._answer.set_videodir(stats["video_library_update"],\
                    self._deejayd)

class GetAudioDir(default_commands._Command):
    name = "getdir"
    method = "post"
    command_args = [{"name":"dir","type":"string","req":False,"default":""}]

    def set_answer(self):
        files_list = self._deejayd.get_audio_dir(self._args["dir"])
        self._answer.set_audiofile_list(files_list, self._args["dir"])

class AudioSearch(default_commands._Command):
    name = "search"
    method = "post"
    command_args = [{"name":"type", "type":"enum_str",
                     "values": ('all','title','genre','filename','artist',
                                'album'),"req":True},
                    {"name":"txt", "type":"string", "req":True}]

    def set_answer(self):
        songs = self._deejayd.audio_search(self._args["txt"],self._args["type"])
        self._answer.set_audiosearch_list(songs.get_medias())

#
# Recorded playlist commands
#
class PlaylistCreate(default_commands.PlaylistCreate):

    def set_answer(self):
        pls_list = self._deejayd.get_playlist_list()
        self._answer.set_playlist_list(pls_list.get_medias())

class MagicPlaylistEdit(default_commands.MagicPlaylistEdit):

    def set_answer(self):
        pl = self._deejayd.get_recorded_playlist(self._args["pl_id"])
        filter = pl.get().get_filter()
        properties = pl.get_properties().get_contents()
        self._answer.set_magic_playlist_infos(self._args["pl_id"],\
                filter.filterlist, properties)

class MagicPlaylistUpdate(default_commands.MagicPlaylistUpdate):

    def set_answer(self):
        # source update
        status = self._deejayd.get_status()
        self._answer.set_mode(status, self._deejayd)

        self._answer.set_msg(_("The magic playlist has been updated"))

class StaticPlaylistAdd(default_commands.StaticPlaylistAdd):

    def set_answer(self):
        pass

#
# Playlist Mode commands
#
class PlaylistAdd(_DefaultAnswer, default_commands.PlaylistAdd): pass
class PlaylistRemove(_DefaultAnswer, default_commands.PlaylistRemove): pass
class PlaylistLoad(_DefaultAnswer, default_commands.PlaylistLoad): pass
class PlaylistMove(_DefaultAnswer, default_commands.PlaylistMove): pass
class PlaylistShuffle(_DefaultAnswer, default_commands.PlaylistShuffle): pass
class PlaylistClear(_DefaultAnswer, default_commands.PlaylistClear): pass

class PlaylistSave(default_commands.PlaylistSave):

    def set_answer(self):
        pls_list = self._deejayd.get_playlist_list()
        self._answer.set_playlist_list(pls_list.get_medias())
        self._answer.set_msg(_("Current playlist has been saved"))

class PlaylistErase(default_commands.PlaylistErase):

    def set_answer(self):
        pls_list = self._deejayd.get_playlist_list()
        self._answer.set_playlist_list(pls_list.get_medias())

        # source update
        status = self._deejayd.get_status()
        self._answer.set_mode(status, self._deejayd)

#
# Panel commands
#
class _PanelAnswer(_DefaultAnswer):

    def set_answer(self):
        self._answer.set_panel(self._deejayd)
        super(_PanelAnswer, self).set_answer()

class PanelUpdateFilter(_DefaultAnswer, default_commands.PanelUpdateFilter):

    def set_answer(self):
        tag = self._args["tag"]
        if "__all__" in self._args["values"]:
            # we maybe remove old filter for this tag, so update all panel
            tag = None
        self._answer.set_panel(self._deejayd, tag)
        super(PanelUpdateFilter, self).set_answer()

class PanelSet(_PanelAnswer, default_commands.PanelSet): pass
class PanelUpdateSearch(_PanelAnswer, default_commands.PanelUpdateSearch): pass
class PanelClear(_PanelAnswer, default_commands.PanelClear): pass
class PanelSort(_DefaultAnswer, default_commands.PanelSort): pass

#
# Queue commands
#
class QueueAdd(_DefaultAnswer, default_commands.QueueAdd): pass
class QueueLoad(_DefaultAnswer, default_commands.QueueLoad): pass
class QueueMove(_DefaultAnswer, default_commands.QueueMove): pass
class QueueRemove(_DefaultAnswer, default_commands.QueueRemove): pass
class QueueClear(_DefaultAnswer, default_commands.QueueClear): pass

#
# Webradio commands
#
class WebradioAdd(_DefaultAnswer, default_commands.WebradioAdd): pass
class WebradioRemove(_DefaultAnswer, default_commands.WebradioRemove): pass
class WebradioClear(_DefaultAnswer, default_commands.WebradioClear): pass

#
# Video commands
#
class SetVideo(_DefaultAnswer, default_commands.SetVideo):
    pass

#
# Dvd commands
#
class DvdLoad(_DefaultAnswer, default_commands.DvdLoad):
    pass

###########################################################################
# Build the list of available commands
commands = {}

import sys
thismodule = sys.modules[__name__]
for itemName in dir(thismodule):
    try:
        item = getattr(thismodule, itemName)
        commands[item.name] = item
    except AttributeError:
        pass

# vim: ts=4 sw=4 expandtab
