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

from genshi.filters import HTMLFormFiller
from deejayd.ui.config import DeejaydConfig
from deejayd.webui import commands as default_commands

#
# Specific commands for mobile webui
#
class Init(default_commands._Command):
    name = "init"

    def set_answer(self):
        self._answer.set_config()
        self._answer.set_page("now_playing")

class SetPage(default_commands._Command):
    name = "setPage"
    command_args = [{"name": "page", "type": "enum_str",\
        "values": ("now_playing","mode_list","current_mode"),"req": True}]

    def set_answer(self):
        self._answer.set_page(self._args["page"])

class MediaList(default_commands._Command):
    name = "mediaList"
    command_args = [{"name": "page", "type": "int","req": True}]

    def set_answer(self):
        self._answer.build_medialist(int(self._args["page"]))

class ExtraPage(default_commands._Command):
    name = "extraPage"
    command_args = [{"name": "page", "type": "str","req": True}]

    def set_answer(self):
        self._answer.load_templates("modes")
        content = None
        if self._args["page"] == "options":
            status = self._deejayd.get_status().get_contents()
            title = _("Options")
            source = status["mode"]
            content = self._answer.get_template("options.thtml").\
                    generate(s=source)
            # set form input value
            form = HTMLFormFiller(data={\
                    "select-playorder": status[source+"playorder"],\
                    "checkbox-repeat": str(status[source+"repeat"])})
            content = content | form
            content = content.render('xhtml')
        elif self._args["page"] == "audio_dir":
            self._answer.build_library("audio", "")
            title = _("Audio Library")
        elif self._args["page"] == "video_dir":
            self._answer.build_library("video", "")
            title = _("Video Library")
        elif self._args["page"] == "video_search":
            title = _("Video Search")
            content = self._answer.get_template("video_search.thtml").\
                    generate().render('xhtml')
        elif self._args["page"] == "wb_form":
            title = _("Add Webradio")
            content = self._answer.get_template("wb_form.thtml").\
                    generate().render('xhtml')

        self._answer.extra_page(title)
        if content: self._answer.set_block("mode-extra-content",content)

########################################################################
# player commands
########################################################################

class PlayerAnswer:

    def set_answer(self):
        self._answer.refresh_page("now_playing")

class PlayToggle(PlayerAnswer, default_commands.PlayToggle): pass
class Stop(PlayerAnswer, default_commands.Stop): pass
class Next(PlayerAnswer, default_commands.Next): pass
class Previous(PlayerAnswer, default_commands.Previous): pass
class Volume(PlayerAnswer, default_commands.Volume): pass
class Repeat(default_commands.Repeat): pass
class PlayOrder(default_commands.PlayOrder): pass

class GoTo(default_commands.GoTo):

    def set_answer(self):
        self._answer.set_page("now_playing")

class SetMode(default_commands.SetMode):

    def set_answer(self):
        self._answer.set_page("current_mode")

########################################################################
class MedialistAnswer:

    def set_answer(self):
        self._answer.build_medialist()

class GetLibraryDir(default_commands.GetLibraryDir):

    def set_answer(self):
        self._answer.build_library(self._args["type"], self._args["dir"],\
                self._args["page"])

########################################################################
# playlist commands
########################################################################

class PlaylistAdd(MedialistAnswer, default_commands.PlaylistAdd):

    def set_answer(self):
        super(PlaylistAdd, self).set_answer()
        self._answer.set_msg(_("Files has been loaded to the playlist"))

class PlaylistShuffle(MedialistAnswer, default_commands.PlaylistShuffle): pass
class PlaylistClear(MedialistAnswer, default_commands.PlaylistClear): pass
class PlaylistRemove(MedialistAnswer, default_commands.PlaylistRemove): pass

########################################################################
# webradio commands
########################################################################

class WebradioAdd(MedialistAnswer, default_commands.WebradioAdd): pass
class WebradioClear(MedialistAnswer, default_commands.WebradioClear): pass
class WebradioRemove(MedialistAnswer, default_commands.WebradioRemove): pass

########################################################################
# video commands
########################################################################

class SetVideo(MedialistAnswer, default_commands.SetVideo): pass

########################################################################
# dvd commands
########################################################################

class DvdLoad(MedialistAnswer, default_commands.DvdLoad): pass

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
