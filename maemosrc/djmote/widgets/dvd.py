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

import os
import gtk
from deejayd.net.client import DeejaydError
from djmote.utils.decorators import gui_callback
from djmote.widgets._base import _BaseSourceBox, format_time

class DvdBox(_BaseSourceBox):
    use_toggled = False
    _toolbar_items = [
        (gtk.STOCK_REFRESH, "reload"),
        ]

    def __init__(self, player):
        self._signals = [ ("dvd.update", "update") ]
        self._signal_ids = []
        _BaseSourceBox.__init__(self, player)

    def update(self, signal = None):
        self.server.get_dvd_content().add_callback(self.cb_update)

    def reload(self, widget):
        self.set_loading()
        self.server.dvd_reload().add_callback(self.cb_dvd_reload)

    @gui_callback
    def cb_dvd_reload(self, answer):
        try: answer.get_contents()
        except DeejaydError, err:
            model = self.tree_view.get_model()
            model.clear()
            model.append([False, 0, err, False])

    @gui_callback
    def cb_update(self, answer):
        try: content = answer.get_dvd_contents()
        except DeejaydError, err:
            self.error(err)
            return

        model = self.tree_view.get_model()
        model.clear()
        i = 0
        for track in content['track']:
            text = "  Title %s\n\tlength : <i>%s</i>"\
                % (track['ix'], format_time(int(track['length'])))
            model.append([False, int(track["ix"]), text, i%2])
            i+=1


# vim: ts=4 sw=4 expandtab
