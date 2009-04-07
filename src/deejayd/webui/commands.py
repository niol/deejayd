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

from deejayd.utils import str_encode

class ArgError(Exception): pass

class _Command(object):
    method = "get"
    command_args = []

    def __init__(self, deejayd, ans):
        self._answer = ans
        self._deejayd = deejayd
        self._args = {}

    def _encode_arg(self, arg):
        # only accept argument encoded to utf-8
        return str_encode(arg is not None and arg or "")

    def argument_validation(self, http_args):
        for arg in self.command_args:
            if arg['name'] in http_args:
                # format http parms
                value = http_args[arg['name']]
                if "mult" in arg.keys() and arg["mult"]:
                    if not isinstance(value, list): value = [value]
                    try:
                        self._args[arg['name']] = [self._encode_arg(v)\
                             for v in value]
                    except UnicodeError:
                        continue
                else:
                    if isinstance(value, list): value = value[0]
                    try: self._args[arg['name']] = self._encode_arg(value)
                    except UnicodeError:
                        continue
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

                    elif arg['type'] == "magic_pls_infos":
                        from deejayd.xmlobject import ET
                        from deejayd import mediafilters
                        try: tree = ET.XML(v)
                        except:
                            raise ArgError(_("bad 'magic_pls_infos' arg"))
                        value = {"filters": [], "properties": {}}
                        for item in tree.getiterator(tag = 'filter'):
                            filter_name = item.find('operator').text
                            try: ft_cls = mediafilters.NAME2BASIC[filter_name]
                            except KeyError:
                                raise ArgError(_("basic filter not found"))
                            value["filters"].append(\
                                    ft_cls(item.find('tag').text,\
                                    item.find('value').text))
                        for item in tree.getiterator(tag = 'property'):
                            value["properties"][item.attrib['id']] = item.text
                        self._args[arg['name']] = value

            elif arg['req']:
                raise ArgError(_("Arg %s is mising") % arg['name'])
            else:
                self._args[arg['name']] = arg['default']

    def execute(self): pass
    def set_answer(self): pass

########################################################################
########################################################################

class SetMode(_Command):
    name = "setMode"
    command_args = [{"name": "mode", "type": "string", "req": True}]

    def execute(self):
        self._deejayd.set_mode(self._args["mode"]).get_contents()

class _ControlCommand(_Command):

    def execute(self):
        cmd = getattr(self._deejayd, self.__class__.name)
        cmd().get_contents()

class PlayToggle(_ControlCommand): name = "play_toggle"
class Stop(_ControlCommand): name = "stop"
class Next(_ControlCommand): name = "next"
class Previous(_ControlCommand): name = "previous"

class Volume(_Command):
    name = "setVol"
    command_args = [
      {"name":"volume", "type":"enum_int", "req":True, "values":range(0,101)}]

    def execute(self):
        self._deejayd.set_volume(int(self._args["volume"])).get_contents()

class GoTo(_Command):
    name = "goto"
    command_args = [{"name": "id", "type": "regexp",\
            "value":"^\w{1,}|\w{1,}\.\w{1,}$","req": True},
          {"name": "id_type", "type": "string", "req": False, "default": "id"},
          {"name":"source", "type": "string", "req": False, "default": None}]

    def execute(self):
        self._deejayd.go_to(self._args["id"], self._args["id_type"], \
            self._args["source"]).get_contents()

class Seek(_Command):
    name = "setTime"
    command_args = [{"name": "time", "type": "int", "req": True}]

    def execute(self):
        status = self._deejayd.get_status()
        if status["state"] != "stop":
            self._deejayd.seek(self._args["time"])

class Repeat(_Command):
    name = "repeat"
    command_args = [{"name":"source","type":"enum_str","req":True,\
                     "values":("panel","playlist","video")},\
                     {"name":"value","type":"enum_int","req":False,\
                      "values":(0,1),"default": None}]

    def execute(self):
        status = self._deejayd.get_status()
        if self._args["value"] == None:
            val = status[self._args["source"]+"repeat"] == 1 and (0,) or (1,)
        else:
            val = (int(self._args["value"]),)
        self._deejayd.set_option(self._args["source"],\
            "repeat",val[0]).get_contents()

class PlayOrder(_Command):
    name = "playorder"
    method = "post"
    command_args = [{"name":"source","type":"enum_str","req":True,\
                     "values":("panel","playlist","video","queue")},
                    {"name":"value","type":"enum_str","req":True,\
                     "values":("inorder","onemedia","random",\
                               "random-weighted")}]

    def execute(self):
        self._deejayd.set_option(self._args["source"],\
            "playorder",self._args["value"]).get_contents()

class PlayerOption(_Command):
    name = "setPlayerOption"
    command_args = [{"name": "option_name", "type": "str", "req": True},
        {"name": "set_type", "type": "enum_str",\
         "values": ("up", "down", "value"), "req": False, "default": "value"},
        {"name": "option_value", "type": "int", "req": True}]

    def execute(self):
        if self._args["set_type"] == "value":
            val = int(self._args["option_value"])
        else:
            current = self._deejayd.get_current().get_medias()
            try: current = current[0]
            except (IndexError, TypeError): return
            if self._args["option_name"] not in current.keys():
                return
            val = current[self._args["option_name"]]
            if self._args["set_type"] == "up":
                val += int(self._args["option_value"])
            else: val -= int(self._args["option_value"])

        self._deejayd.set_player_option(self._args["option_name"], val).\
            get_contents()

class MediaRating(_Command):
    name = 'setMediaRating'
    method = "post"
    command_args = [{"name":"type", "type":"string", "req":True},
                    {"name": "value", "type": "enum_int",\
                     "values":range(0, 5), "req": True},
                    {"name":"ids", "type":"int", "mult":True, "req": True}]

    def execute(self):
        self._deejayd.set_media_rating(self._args["ids"],\
            self._args["value"], self._args["type"]).get_contents()

########################################################################
########################################################################
class GetLibraryDir(_Command):
    name = "getdir"
    method = "post"
    command_args = [{"name":"dir","type":"string","req":False,"default":""},\
        {"name":"type","type":"enum_str","values":("video","audio"),\
            "req":False,"default":"audio"},\
        {"name":"page", "type":"int", "req":False, "default":1}]

########################################################################
########################################################################
class PlaylistCreate(_Command):
    name = "playlistCreate"
    method = "post"
    command_args = [{"name":"name","type":"string","req":True},\
      {"name":"type","type":"enum_str","values":("static","magic"),"req":True},\
      {"name": "infos","type":"magic_pls_infos","req":False,"default":None}]

    def execute(self):
        pl_infos = self._deejayd.create_recorded_playlist(self._args["name"],\
                self._args["type"]).get_contents()
        if self._args["type"] == 'magic':
            if self._args["infos"] == None:
                raise ArgError(_("infos argument needed for magic playlist"))
            pl = self._deejayd.get_recorded_playlist(pl_infos["pl_id"],\
                    pl_infos["name"], pl_infos["type"])
            for filter in self._args["infos"]["filters"]:
                pl.add_filter(filter).get_contents()
            for k, v in self._args["infos"]["properties"].items():
                pl.set_property(k, v).get_contents()

class MagicPlaylistEdit(_Command):
    name = "magicPlaylistEdit"
    method = "post"
    command_args = [{"name":"pl_id","type":"int","req":True}]

    def execute(self):
        pass

class MagicPlaylistUpdate(_Command):
    name = "magicPlaylistUpdate"
    method = "post"
    command_args = [{"name":"pl_id","type":"int","req":True},\
            {"name": "infos","type":"magic_pls_infos","req":True}]

    def execute(self):
        pl = self._deejayd.get_recorded_playlist(self._args["pl_id"])
        if pl.type != "magic":
            raise ArgError(_("Not a magic playlist"))

        # get current filters and properties
        properties = pl.get_properties()
        rec_filters = pl.get().get_filter().filterlist

        for filter in self._args["infos"]["filters"]:
            found = False
            for rec_filter in rec_filters:
                if rec_filter.equals(filter):
                    found = True
                    rec_filters.remove(rec_filter)
                    break
            if not found: pl.add_filter(filter).get_contents()
        for rec_filter in rec_filters:
            pl.remove_filter(rec_filter).get_contents()

        for k, v in self._args["infos"]["properties"].items():
            if properties[k] != v:
                pl.set_property(k, v).get_contents()

class StaticPlaylistAdd(_Command):
    name = "staticPlaylistAdd"
    method = "post"
    command_args = [{"name":"values","type":"string","req":True,"mult": True},\
                    {"name":"pl_id","type":"int","req":True},
                    {"name":"type","type":"enum_str",\
                     "values": ('path','id'),"req":False, "default": "path"}]

    def execute(self):
        pls = self._deejayd.get_recorded_playlist(self._args["pl_id"])
        if self._args["type"] == "id":
            try: values = map(int, self._args["values"])
            except (TypeError, ValueError):
                raise ArgError(_("Ids arg must be integer"))
            pls.add_songs(values).get_contents()
        else:
            pls.add_paths(self._args["values"]).get_contents()

########################################################################
########################################################################
class PlaylistAdd(_Command):
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

class PlaylistRemove(_Command):
    name = "playlistRemove"
    method = "post"
    command_args = [{"name":"ids","type":"int","req":True,"mult":True},]

    def execute(self):
        pls = self._deejayd.get_playlist()
        pls.del_songs(self._args["ids"]).get_contents()

class PlaylistLoad(_Command):
    name = "playlistLoad"
    method = "post"
    command_args = [{"name":"pls_ids","type":"int","req":True,"mult":True},\
        {"name":"pos","type":"int","req":True}]

    def execute(self):
        pos = int(self._args["pos"])
        if pos == -1: pos = None

        pls = self._deejayd.get_playlist()
        pls.loads(self._args["pls_ids"],pos).get_contents()

class PlaylistMove(_Command):
    name = "playlistMove"
    method = "post"
    command_args = [{"name":"ids","type":"int","req":True,"mult": True},
                    {"name":"new_pos","type":"int","req":True}]

    def execute(self):
        ids = [int(id) for id in self._args["ids"]]
        pls = self._deejayd.get_playlist()
        pls.move(ids, int(self._args["new_pos"])).get_contents()

class PlaylistSave(_Command):
    name = "playlistSave"
    method = "post"
    command_args = [{"name":"name","type":"string","req":True}]

    def execute(self):
        pls = self._deejayd.get_playlist()
        pls.save(self._args["name"]).get_contents()

class PlaylistErase(_Command):
    name = "playlistErase"
    method = "post"
    command_args = [{"name":"pl_ids","type":"int","req":True,"mult":True}]

    def execute(self):
        self._deejayd.erase_playlist(self._args["pl_ids"]).get_contents()

class PlaylistShuffle(_Command):
    name = "playlistShuffle"

    def execute(self):
        pls = self._deejayd.get_playlist()
        pls.shuffle().get_contents()

class PlaylistClear(_Command):
    name = "playlistClear"

    def execute(self):
        pls = self._deejayd.get_playlist()
        pls.clear().get_contents()

########################################################################
########################################################################
class PanelSet(_Command):
    name = "panelSet"
    method = "post"
    command_args = [{"name":"value","type":"string","req":False,"default":""},\
        {"name":"type","type":"enum_str","values": ('panel','playlist'),\
         "req":True}]

    def execute(self):
        panel = self._deejayd.get_panel()
        panel.set_active_list(self._args["type"], self._args["value"])

class PanelUpdateFilter(_Command):
    name = "panelUpdateFilter"
    method = "post"
    command_args = [{"name":"values","type":"string","req":True,"mult":True},\
        {"name":"tag","type":"enum_str",\
         "values":("genre","various_artist","artist","album"),"req":True},]

    def execute(self):
        panel = self._deejayd.get_panel()
        if "__all__" in self._args["values"]:
            panel.remove_panel_filters(self._args["tag"])
        else:
            panel.set_panel_filters(self._args["tag"], self._args["values"])

class PanelUpdateSearch(_Command):
    name = "panelUpdateSearch"
    method = "post"
    command_args = [{"name":"value","type":"string","req":True},\
        {"name":"tag","type":"enum_str",\
         "values":("genre","artist","album","title","all"),"req":True},]

    def execute(self):
        panel = self._deejayd.get_panel()
        if self._args["value"] == "":
            panel.clear_search_filter()
        else:
            panel.set_search_filter(self._args["tag"], self._args["value"])

class PanelClear(_Command):
    name = "panelClear"

    def execute(self):
        panel = self._deejayd.get_panel()
        panel.clear_panel_filters()
        panel.clear_search_filter()

class PanelSort(_Command):
    name = "panelSort"
    method = "post"
    command_args = [
        {"name":"direction","type":"enum_str",\
         "values":("ascending","descending", "none"),"req":True},\
        {"name":"tag","type":"enum_str",\
         "values":("genre","artist","album","title","rating"),"req":True},]

    def execute(self):
        panel = self._deejayd.get_panel()
        if self._args["direction"] != "none":
            panel.set_sorts([(self._args["tag"], self._args["direction"])])
        else:
            panel.set_sorts([])

########################################################################
########################################################################
class QueueAdd(_Command):
    name = "queueAdd"
    method = "post"
    command_args = [{"name":"values","type":"string","req":True,"mult":True},\
        {"name":"pos","type":"int","req":True},\
        {"name":"type","type":"enum_str",\
         "values": ('path','id'),"req":False, "default": "path"}]

    def execute(self):
        pos = int(self._args["pos"])
        if pos == -1: pos = None

        queue = self._deejayd.get_queue()
        if self._args["type"] == "id":
            try: values = map(int, self._args["values"])
            except (TypeError, ValueError):
                raise ArgError(_("Ids arg must be integer"))
            queue.add_songs(values, pos).get_contents()
        else:
            queue.add_paths(self._args["values"], pos).get_contents()

class QueueLoad(_Command):
    name = "queueLoad"
    method = "post"
    command_args = [{"name":"pls_ids","type":"int","req":True,"mult":True},\
                    {"name":"pos","type":"int","req":True}]

    def execute(self):
        pos = int(self._args["pos"])
        if pos == -1: pos = None

        queue = self._deejayd.get_queue()
        queue.load_playlists(self._args["pls_ids"],pos).get_contents()

class QueueMove(_Command):
    name = "queueMove"
    method = "post"
    command_args = [{"name":"ids","type":"int","req":True,"mult": True},
                    {"name":"new_pos","type":"int","req":True}]

    def execute(self):
        ids = [int(id) for id in self._args["ids"]]
        queue = self._deejayd.get_queue()
        queue.move(ids, int(self._args["new_pos"])).get_contents()

class QueueRemove(_Command):
    name = "queueRemove"
    method = "post"
    command_args = [{"name":"ids","type":"int","req":True,"mult":True},]

    def execute(self):
        queue = self._deejayd.get_queue()
        queue.del_songs(self._args["ids"]).get_contents()

class QueueClear(_Command):
    name = "queueClear"

    def execute(self):
        queue = self._deejayd.get_queue()
        queue.clear().get_contents()

########################################################################
########################################################################
class WebradioAdd(_Command):
    name = "webradioAdd"
    method = "post"
    command_args = [{"name":"name","type":"string","req":True},\
                    {"name":"url","type":"string","req":True},]

    def execute(self):
        wb = self._deejayd.get_webradios()
        wb.add_webradio(self._args["name"], self._args["url"]).get_contents()

class WebradioClear(_Command):
    name = "webradioClear"

    def execute(self):
        wb = self._deejayd.get_webradios()
        wb.clear().get_contents()

class WebradioRemove(_Command):
    name = "webradioRemove"
    method = "post"
    command_args = [{"name":"ids","type":"int","req":True,"mult":True},]

    def execute(self):
        wb = self._deejayd.get_webradios()
        wb.delete_webradios(self._args["ids"]).get_contents()

########################################################################
########################################################################
class SetVideo(_Command):
    name = "videoset"
    method = "post"
    command_args = [{"name":"value", "type":"str", "req":False, "default":""},
            {"name":"type","type":"enum_str","values":("directory","search"),\
            "req":False,"default":"directory"},]

    def execute(self):
        video = self._deejayd.get_video()
        video.set(self._args["value"], self._args["type"]).get_contents()

class VideoSort(_Command):
    name = "videoSort"
    method = "post"
    command_args = [
        {"name":"direction","type":"enum_str",\
         "values":("ascending","descending", "none"),"req":True},\
        {"name":"tag","type":"enum_str",\
         "values":("title","rating","length"),"req":True},]

    def execute(self):
        video = self._deejayd.get_video()
        if self._args["direction"] != "none":
            video.set_sorts([(self._args["tag"], self._args["direction"])])
        else:
            video.set_sorts([])

########################################################################
########################################################################
class DvdLoad(_Command):
    name = "dvdLoad"

    def execute(self):
        self._deejayd.dvd_reload().get_contents()


# vim: ts=4 sw=4 expandtab
