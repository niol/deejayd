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

class Init(default_commands._Command):
    name = "init"

class SetPage(default_commands._Command):
    name = "setPage"
    command_args = [{"name": "page", "type": "enum_str",\
        "values": ("now_playing","mode_list","current_mode"),"req": True}]

class MediaList(default_commands._Command):
    name = "mediaList"
    command_args = [{"name": "page", "type": "int","req": True}]

class ExtraPage(default_commands._Command):
    name = "extraPage"
    command_args = [{"name": "page", "type": "str","req": True}]

commands = {}
# first add default commands
for itemName in dir(default_commands):
    try:
        item = getattr(default_commands, itemName)
        commands[item.name] = item
    except AttributeError:
        pass

import sys
thismodule = sys.modules[__name__]
for itemName in dir(thismodule):
    try:
        item = getattr(thismodule, itemName)
        commands[item.name] = item
    except AttributeError:
        pass

# vim: ts=4 sw=4 expandtab
