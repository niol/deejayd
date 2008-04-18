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

import gobject, gtk
from djmote.widgets import playlist, webradio, video, dvd
from djmote.widgets._base import _BaseWidget
from djmote.utils.decorators import gui_callback

class ModeBox(gtk.VBox, _BaseWidget):
    _supported_mode_ = {
        "playlist": playlist.PlaylistBox,
        "video": video.VideoBox,
        "webradio": webradio.WebradioBox,
        "dvd": dvd.DvdBox
        }

    def __init__(self, ui):
        gtk.VBox.__init__(self)

        self._signals = [ ("mode", "update_mode") ]
        self._signal_ids = []
        self.server = ui.get_server()
        self.__content = None

        # Signals
        ui.connect("connected",self.init_mode)
        ui.connect("disconnected",self.disconnect)

    def init_mode(self, ui, status):
        # subscribe to signal
        self.subscribe()
        self.__build(status["mode"])

    def update_mode(self, signal):
        self.server.get_status().add_callback(self.cb_update_mode)

    def disconnect(self, ui):
        self._signal_ids = []
        if self.__content:
            self.__content.main_box.destroy()
            self.__content = None

    def __build(self, mode):
        self.__content = self._supported_mode_[mode](self.server)
        self.pack_start(self.__content.main_box)
        self.show_all()

    @gui_callback
    def cb_update_mode(self, answer):
        try: status = answer.get_contents()
        except DeejaydError, err:
            self.error(err)
        else:
            if self.__content: self.__content.destroy()
            self.__build(status["mode"])

# vim: ts=4 sw=4 expandtab
