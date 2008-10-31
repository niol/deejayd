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

class ArgError(Exception): pass

class _Command(object):
    method = "get"
    command_args = []

    def __init__(self, deejayd):
        self._deejayd = deejayd
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

    def execute(self): pass

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

class PlaylistRemove(_Command):
    name = "playlistRemove"
    method = "post"
    command_args = [{"name":"ids","type":"int","req":True,"mult":True},]

    def execute(self):
        pls = self._deejayd.get_playlist()
        pls.del_songs(self._args["ids"]).get_contents()

########################################################################
########################################################################
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

# vim: ts=4 sw=4 expandtab
