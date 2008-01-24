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

class ArgError(Exception): pass

class _UnknownCommand:
    method = "get"
    command_args = []

    def __init__(self, deejayd, answer):
        self._deejayd = deejayd
        self._answer = answer
        self._args = {}

    def argument_validation(self, http_args):
        for arg in self.command_args:
            if arg['name'] in http_args:
                # format http parms
                value = http_args[arg['name']]
                if "mult" in arg.keys() and arg["mult"]:
                    if not isinstance(value, list): value = [value]
                    self._args[arg['name']] = value
                else:
                    if isinstance(value, list): value = value[0]
                    self._args[arg['name']] = value
                    value = [value]

                for v in value:
                    if arg['type'] == "string":
                        try: v.split()
                        except AttributeError:
                            raise ArgError(_("Arg %s (%s) is not a string") % \
                                (arg['name'], str(v)))

                    elif arg['type'] == "int":
                        try: v = int(v)
                        except (ValueError,TypeError):
                            raise ArgError(_("Arg %s (%s) is not a int") %\
                                (arg['name'], str(v)))

                    elif arg['type'] == "enum_str":
                        if v not in arg['values']:
                            raise ArgError(\
                                _("Arg %s (%s) is not in the possible list")\
                                % (arg['name'],str(v)))

                    elif arg['type'] == "enum_int":
                        try: v = int(v)
                        except (ValueError,TypeError):
                            raise ArgError(_("Arg %s (%s) is not a int") %\
                                (arg['name'], str(v)))
                        else:
                            if v not in arg['values']:
                                raise ArgError(\
                                    _(\
                                    "Arg %s (%s) is not in the possible list")\
                                    % (arg['name'],str(v)))

                    elif arg['type'] == "regexp":
                        import re
                        if not re.compile(arg['value']).search(v):
                            raise ArgError(\
                            _("Arg %s (%s) not match to the regular exp (%s)") %
                                (arg['name'],str(v),arg['value']))

            elif arg['req']:
                raise ArgError(_("Arg %s is mising") % arg['name'])
            else:
                self._args[arg['name']] = arg['default']

    def default_result(self):
        status = self._deejayd.get_status()
        # player update
        cur = None
        if status["state"] != "stop":
            cur = self._deejayd.get_current().get_medias()
            cur = cur[0]
        self._answer.set_player(status, cur)

        # source update
        self._answer.set_playlist(status, self._deejayd)
        self._answer.set_queue(status, self._deejayd)
        if "webradio" in status.keys():
            self._answer.set_webradio(status, self._deejayd)
        if "dvd" in status.keys():
            self._answer.set_dvd(status, self._deejayd)
        if "video" in status.keys():
            self._answer.set_video(status, self._deejayd)

        # video library update
        stats = self._deejayd.get_stats()
        if "video_library_update" in stats.keys():
            self._answer.set_videodir(int(stats["video_library_update"]),\
                self._deejayd)

    def execute(self):
        raise NotImplementedError

class Init(_UnknownCommand):
    name = "init"

    def execute(self):
        status = self._deejayd.get_status()
        # available modes
        av_modes = self._deejayd.get_mode()
        self._answer.set_available_modes(av_modes)

        # current mode
        self._answer.set_view_mode(status["mode"])

        # locale string
        strings = {"confirm": _('Are you sure ?'),
                   "missParm": _('It misses a parameter !'),
                   "replacePls": _('Do you want to replace this playlist ?')}
        self._answer.set_locale_strings(strings)

        # config parms
        config = DeejaydConfig()
        refresh = config.get('webui','refresh')
        self._answer.set_config({"refresh": refresh})

        # audio files list
        files_list = self._deejayd.get_audio_dir("")
        self._answer.set_audiofile_list(files_list, "")

        # playlist list
        pls_list = self._deejayd.get_playlist_list()
        self._answer.set_playlist_list(pls_list.get_medias())

class Refresh(_UnknownCommand):
    name = "refresh"
    def execute(self): pass

class SetMode(_UnknownCommand):
    name = "setMode"
    command_args = [{"name": "mode", "type": "string", "req": True}]

    def execute(self):
        self._deejayd.set_mode(self._args["mode"]).get_contents()
        self._answer.set_view_mode(self._args["mode"])

#
# Player controls
#
class PlayToggle(_UnknownCommand):
    name = "playtoggle"

    def execute(self):
        self._deejayd.play_toggle().get_contents()

class GoTo(_UnknownCommand):
    name = "goto"
    command_args = [{"name": "id", "type": "regexp",\
            "value":"^\w{1,}|\w{1,}\.\w{1,}$","req": True},
          {"name": "id_type", "type": "string", "req": False, "default": "id"},
          {"name":"source", "type": "string", "req": False, "default": None}]

    def execute(self):
        self._deejayd.go_to(self._args["id"], self._args["id_type"], \
            self._args["source"]).get_contents()

class Stop(_UnknownCommand):
    name = "stop"

    def execute(self):
        self._deejayd.stop().get_contents()

class Next(_UnknownCommand):
    name = "next"

    def execute(self):
        self._deejayd.next().get_contents()

class Previous(_UnknownCommand):
    name = "previous"

    def execute(self):
        self._deejayd.previous().get_contents()

class _Options(_UnknownCommand):
    def execute(self):
        status = self._deejayd.get_status()
        val = status[self.__class__.name] == 1 and (0,) or (1,)
        self._deejayd.set_option(self.__class__.name,val[0]).get_contents()

class Random(_Options):
    name = "random"

class Repeat(_Options):
    name = "repeat"

class Volume(_UnknownCommand):
    name = "setVol"
    command_args = [
        {"name":"volume", "type":"enum_int", "req":True, "values":range(0,101)}]

    def execute(self):
        self._deejayd.set_volume(int(self._args["volume"])).get_contents()

class Seek(_UnknownCommand):
    name = "setTime"
    command_args = [{"name": "time", "type": "int", "req": True}]

    def execute(self):
        status = self._deejayd.get_status()
        if status["state"] != "stop":
            self._deejayd.seek(self._args["time"])

class AudioLang(_UnknownCommand):
    name = "setAlang"
    command_args = [{"name": "lang_idx", "type": "int", "req": True}]

    def execute(self):
        self._deejayd.set_alang(self._args["lang_idx"]).get_contents()

class SubtitleLang(_UnknownCommand):
    name = "setSlang"
    command_args = [{"name": "lang_idx", "type": "int", "req": True}]

    def execute(self):
        self._deejayd.set_slang(self._args["lang_idx"]).get_contents()

#
# Library commands
#
class _Library(_UnknownCommand):
    def default_result(self): pass

class AudioLibraryUpdate(_Library):
    name = "audioUpdate"

    def execute(self):
        rs = self._deejayd.update_audio_library()
        self._answer.set_update_library(rs["audio_updating_db"], "audio")

class VideoLibraryUpdate(_Library):
    name = "videoUpdate"

    def execute(self):
        rs = self._deejayd.update_video_library()
        self._answer.set_update_library(rs["video_updating_db"], "video")

class AudioUpdateCheck(_Library):
    name = "audio_update_check"
    command_args = [{"name": "id", "type": "int", "req": True}]

    def execute(self):
        status = self._deejayd.get_status()
        if "audio_updating_db" in status.keys() and \
                int(status["audio_updating_db"]) == int(self._args["id"]):
            self._answer.set_update_library(self._args["id"], "audio")
        else:
            self._answer.set_update_library(self._args["id"], "audio", "0")
            self._answer.set_msg(_("The audio library has been updated"))

            files_list = self._deejayd.get_audio_dir()
            self._answer.set_audiofile_list(files_list, "")

class VideoUpdateCheck(_Library):
    name = "video_update_check"
    command_args = [{"name": "id", "type": "int", "req": True}]

    def execute(self):
        status = self._deejayd.get_status()
        if "video_updating_db" in status.keys() and \
                int(status["video_updating_db"]) == int(self._args["id"]):
            self._answer.set_update_library(self._args["id"], "video")
        else:
            self._answer.set_update_library(self._args["id"], "video", "0")
            self._answer.set_msg(_("The video library has been updated"))

            stats = self._deejayd.get_stats()
            self._answer.set_videodir(stats["video_library_update"],\
                self._deejayd)

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
        files_list = self._deejayd.audio_search(self._args["txt"],
                self._args["type"])
        self._answer.set_audiofile_list(files_list)

#
# Playlist commands
#
class PlaylistAdd(_UnknownCommand):
    name = "playlistAdd"
    method = "post"
    command_args = [{"name":"path","type":"string","req":True,"mult": True},\
        {"name":"name","type":"string","req":False,"default":None},
        {"name":"pos","type":"int","req":False,"default":-1}]

    def execute(self):
        pos = int(self._args["pos"])
        if pos == -1: pos = None

        pls = self._deejayd.get_playlist(self._args["name"])
        pls.add_songs(self._args["path"],pos).get_contents()

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
    command_args = [{"name":"pls_name","type":"string","req":True,"mult":True},\
        {"name":"name","type":"string","req":False,"default":None},
        {"name":"pos","type":"int","req":True}]

    def execute(self):
        pos = int(self._args["pos"])
        if pos == -1: pos = None

        pls = self._deejayd.get_playlist(self._args["name"])
        pls.loads(self._args["pls_name"],pos).get_contents()

class PlaylistMove(_UnknownCommand):
    name = "playlistMove"
    method = "post"
    command_args = [{"name":"ids","type":"int","req":True,"mult": True},
                    {"name":"new_pos","type":"int","req":True}]

    def execute(self):
        ids = [int(id) for id in self._args["ids"]]
        pls = self._deejayd.get_playlist()
        pls.move(ids, int(self._args["new_pos"])).get_contents()

class PlaylistSave(_UnknownCommand):
    name = "playlistSave"
    method = "post"
    command_args = [{"name":"name","type":"string","req":True}]

    def default_result(self):
        pls_list = self._deejayd.get_playlist_list()
        self._answer.set_playlist_list(pls_list.get_medias())

    def execute(self):
        pls = self._deejayd.get_playlist()
        pls.save(self._args["name"]).get_contents()

class PlaylistErase(_UnknownCommand):
    name = "playlistErase"
    method = "post"
    command_args = [{"name":"name","type":"string","req":True,"mult":True}]

    def default_result(self):
        pls_list = self._deejayd.get_playlist_list()
        self._answer.set_playlist_list(pls_list.get_medias())

    def execute(self):
        self._deejayd.erase_playlist(self._args["name"]).get_contents()

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
# Queue commands
#
class QueueAdd(_UnknownCommand):
    name = "queueAdd"
    method = "post"
    command_args = [{"name":"path","type":"string","req":True,"mult":True},\
              {"name":"type", "type":"enum_str", "values":("audio", "video"),\
               "req":False, "default":"audio"},
              {"name":"pos","type":"int","req":True}]

    def execute(self):
        pos = int(self._args["pos"])
        if pos == -1: pos = None

        queue = self._deejayd.get_queue()
        queue.add_medias(self._args["path"],\
            self._args["type"],pos).get_contents()

class QueueLoad(_UnknownCommand):
    name = "queueLoad"
    method = "post"
    command_args = [{"name":"pls_name","type":"string","req":True,"mult":True},\
                    {"name":"pos","type":"int","req":True}]

    def execute(self):
        pos = int(self._args["pos"])
        if pos == -1: pos = None

        queue = self._deejayd.get_queue()
        queue.load_playlists(self._args["pls_name"],pos).get_contents()

class QueueRemove(_UnknownCommand):
    name = "queueRemove"
    method = "post"
    command_args = [{"name":"id","type":"int","req":True},]

    def execute(self):
        queue = self._deejayd.get_queue()
        queue.del_songs(self._args["id"]).get_contents()

class QueueClear(_UnknownCommand):
    name = "queueClear"

    def execute(self):
        queue = self._deejayd.get_queue()
        queue.clear().get_contents()

#
# Webradio commands
#
class WebradioAdd(_UnknownCommand):
    name = "webradioAdd"
    method = "post"
    command_args = [{"name":"name","type":"string","req":True},\
                    {"name":"url","type":"string","req":True},]

    def execute(self):
        wb = self._deejayd.get_webradios()
        wb.add_webradio(self._args["name"], self._args["url"]).get_contents()

class WebradioDelete(_UnknownCommand):
    name = "webradioRemove"
    method = "post"
    command_args = [{"name":"ids","type":"int","req":True,"mult":True},]

    def execute(self):
        wb = self._deejayd.get_webradios()
        wb.delete_webradios(self._args["ids"]).get_contents()

class WebradioClear(_UnknownCommand):
    name = "webradioClear"

    def execute(self):
        wb = self._deejayd.get_webradios()
        wb.clear().get_contents()

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
        self._deejayd.set_video(self._args["value"],\
            self._args["type"]).get_contents()

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
