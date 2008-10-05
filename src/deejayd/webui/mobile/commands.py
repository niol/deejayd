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
from deejayd.webui.commands import _Command

class _UnknownCommand(_Command):
    answer_type = "custom"

    def _set_result(self):
        raise NotImplementedError

    def set_result(self):
        if self.answer_type == "page":
            self._answer.set_page(self._deejayd, self.page_name)
        elif self.answer_type == "custom":
            self._set_result()

class Init(_UnknownCommand):
    answer_type = "page"
    page_name = "now_playing"
    name = "init"

    def execute(self): pass

class Refresh(_UnknownCommand):
    name = "refresh"
    command_args = [{"name": "page", "type": "string", "req": True}]

    def execute(self): pass

class SetPage(_UnknownCommand):
    answer_type = "page"
    name = "setPage"
    command_args = [{"name": "page", "type": "string", "req": True}]

    def execute(self):
        self.page_name = self._args["page"]

class SetMode(_UnknownCommand):
    name = "setMode"
    command_args = [{"name": "mode", "type": "string", "req": True}]
    answer_type = "page"
    page_name = "current_mode"

    def execute(self):
        self._deejayd.set_mode(self._args["mode"]).get_contents()

#
# Player controls
#
class _ControlCommand(_UnknownCommand):

    def _set_result(self):
        self._answer.refresh_page(self._deejayd, "now_playing")

    def execute(self):
        cmd = getattr(self._deejayd, self.__class__.name)
        cmd().get_contents()

class PlayToggle(_ControlCommand): name = "play_toggle"
class Stop(_ControlCommand): name = "stop"
class Next(_ControlCommand): name = "next"
class Previous(_ControlCommand): name = "previous"

class Volume(_ControlCommand):
    name = "setVol"
    command_args = [
        {"name":"volume", "type":"enum_int", "req":True, "values":range(0,101)}]

    def execute(self):
        self._deejayd.set_volume(int(self._args["volume"])).get_contents()

class GoTo(_UnknownCommand):
    name = "goto"
    command_args = [{"name": "id", "type": "regexp",\
            "value":"^\w{1,}|\w{1,}\.\w{1,}$","req": True},
          {"name": "id_type", "type": "string", "req": False, "default": "id"},
          {"name":"source", "type": "string", "req": False, "default": None}]
    answer_type = "page"
    page_name = "now_playing"

    def execute(self):
        self._deejayd.go_to(self._args["id"], self._args["id_type"], \
            self._args["source"]).get_contents()

#
# Library commands
#
class _Library(_UnknownCommand):
    def default_result(self): pass

class GetAudioDir(_Library):
    name = "getdir"
    method = "post"
    command_args = [{"name":"dir","type":"string","req":False,"default":""}]

    def execute(self):
        files_list = self._deejayd.get_audio_dir(self._args["dir"])
        self._answer.set_audiofile_list(files_list, self._args["dir"])

class AudioSearch(_Library):
    name = "search"
    method = "post"
    command_args = [{"name":"type", "type":"enum_str",
                     "values": ('all','title','genre','filename','artist',
                                'album'),"req":True},
                    {"name":"txt", "type":"string", "req":True}]

    def execute(self):
        songs = self._deejayd.audio_search(self._args["txt"],self._args["type"])
        self._answer.set_audiosearch_list(songs.get_medias())

#
# Playlist Mode commands
#
class PlaylistAdd(_UnknownCommand):
    name = "playlistAdd"
    method = "post"
    command_args = [{"name":"values","type":"string","req":True,"mult": True},\
        {"name":"pos","type":"int","req":False,"default":-1},\
        {"name":"type","type":"enum_str",\
         "values": ('path','id'),"req":False, "default": "path"}]

    def execute(self):
        pos = int(self._args["pos"])
        if pos == -1: pos = None

        pls = self._deejayd.get_playlist()
        if self._args["type"] == "id":
            try: values = map(int, self._args["values"])
            except (TypeError, ValueError):
                raise ArgError(_("Ids arg must be integer"))
            pls.add_songs(values, pos).get_contents()
        else:
            pls.add_paths(self._args["values"], pos).get_contents()

class PlaylistRemove(_UnknownCommand):
    name = "playlistRemove"
    method = "post"
    command_args = [{"name":"ids","type":"int","req":True,"mult":True},]

    def execute(self):
        pls = self._deejayd.get_playlist()
        pls.del_songs(self._args["ids"]).get_contents()

class PlaylistLoad(_UnknownCommand):
    name = "playlistLoad"
    method = "post"
    command_args = [{"name":"pls_ids","type":"int","req":True,"mult":True},\
        {"name":"pos","type":"int","req":True}]

    def execute(self):
        pos = int(self._args["pos"])
        if pos == -1: pos = None

        pls = self._deejayd.get_playlist()
        pls.loads(self._args["pls_ids"],pos).get_contents()

class PlaylistShuffle(_UnknownCommand):
    name = "playlistShuffle"

    def execute(self):
        pls = self._deejayd.get_playlist()
        pls.shuffle().get_contents()

class PlaylistClear(_UnknownCommand):
    name = "playlistClear"

    def execute(self):
        pls = self._deejayd.get_playlist()
        pls.clear().get_contents()

#
# Panel commands
#
class PanelSet(_UnknownCommand):
    name = "panelSet"
    method = "post"
    command_args = [{"name":"value","type":"string","req":False,"default":""},\
        {"name":"type","type":"enum_str","values": ('panel','playlist'),\
         "req":True}]

    def execute(self):
        panel = self._deejayd.get_panel()
        panel.set_active_list(self._args["type"], self._args["value"])


class PanelListTag(_UnknownCommand):
    name = "panelUpdateFilter"
    method = "post"
    command_args = [{"name":"value","type":"string","req":True},\
        {"name":"tag","type":"enum_str",\
         "values":("genre","artist","album","title","all"),"req":True},\
        {"name":"type","type":"enum_str","values": ('equals','contains'),\
         "req":True}]

    def execute(self):
        panel = self._deejayd.get_panel()
        if self._args["value"] == "__all__":
            panel.remove_panel_filters(self._args["type"], self._args["tag"])
        elif self._args["value"] == "__compilation__":
            panel.remove_panel_filters(self._args["type"], self._args["tag"])
            panel.update_panel_filters("compilation", "equals", "1")
        else:
            if self._args["tag"] in ("artist", "genre"):
                panel.remove_panel_filters("equals", "compilation")
            panel.update_panel_filters(self._args["tag"],\
                self._args["type"], self._args["value"])

            # remove filter for panels at the right of this tag
            if self._args["type"] == "equals":
                for tg in ('album','artist','album'):
                    if tg == self._args["tag"]:
                        break
                    panel.remove_panel_filters(self._args["type"], tg)

#
# Video commands
#
class SetVideo(_UnknownCommand):
    name = "videoset"
    method = "post"
    command_args = [{"name":"value", "type":"str", "req":False, "default":""},
            {"name":"type","type":"enum_str","values":("directory","search"),\
            "req":False,"default":"directory"},]

    def execute(self):
        video = self._deejayd.get_video()
        video.set(self._args["value"], self._args["type"]).get_contents()

#
# Dvd commands
#
class DvdLoad(_UnknownCommand):
    name = "dvdLoad"

    def execute(self):
        self._deejayd.dvd_reload().get_contents()

###########################################################################
commands = {}

import sys
thismodule = sys.modules[__name__]
for itemName in dir(thismodule):
    try:
        item = getattr(thismodule, itemName)
        commands[item.name] = item
    except AttributeError:
        pass
# Build the list of available commands
