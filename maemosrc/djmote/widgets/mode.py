# Djmote, a graphical deejayd client designed for use on Maemo devices
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

import gtk
from djmote.widgets.playlist import PlaylistBox
from djmote.widgets.webradio import WebradioBox
from djmote.widgets.video import VideoBox
from djmote.widgets.dvd import DvdBox

class ModeBox(gtk.VBox):
    _supported_mode_ = {"playlist": PlaylistBox, "video": VideoBox,\
        "webradio": WebradioBox, "dvd": DvdBox}

    def __init__(self,player):
        gtk.VBox.__init__(self)
        self.__player = player
        self.__content = None

        # Signals
        player.connect("update-status",self.update_status)
        player.connect("connected",self.update_status)
        player.connect("disconnected",self.__destroy)

    def update_status(self, ui, status):
        if self.__content and self.__content["name"] != status["mode"]:
            self.__destroy()
        if not self.__content:
            self.__build(status["mode"])
        self.__content["widget"].update_status(status)

    def __build(self,mode):
        box = self.__class__._supported_mode_[mode](self.__player)

        self.__content = {"name": mode,"widget": box}
        self.pack_start(self.__content["widget"])
        self.show_all()

    def __destroy(self, ui = None):
        if self.__content:
            self.__content["widget"].destroy()
            self.__content = None

# vim: ts=4 sw=4 expandtab
