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

import gtk,gobject,hildon
from djmote import stock, const
from djmote.widgets._base import DjmoteButton, _BaseWidget

class ControlBox(_BaseWidget):

    def __init__(self, ui):
        self.widget = gtk.VBox()
        self.server = ui.get_server()
        self.__timeout = None

        vol_button = VolumeButton(True)
        vol_button.connect("clicked",self.show_volumebar)
        self.widget.pack_end(vol_button, expand = False, fill = False)

        self.__controls = ControlsPanel(ui)
        self.widget.pack_end(self.__controls)

        self.__vsig, self.__timeout = None, None
        self.__volume = hildon.VVolumebar()
        self.__volume.set_level(0)
        self.widget.pack_end(self.__volume)

        # Signals
        self.widget.connect("show",self.post_show_action)
        ui.main_window.connect("key-press-event", self.key_press, ui)
        ui.connect("update-status",self.update_status)
        ui.connect("connected",self.ui_connected)
        ui.connect("disconnected",self.ui_disconnected)

    def key_press(self, main_window, event, ui):
        if not self.server.is_connected(): return False
        if event.keyval == const.KEY_ENTER:
            self.execute(self.server.play_toggle)
        elif event.keyval == const.KEY_LEFT:
            self.execute(self.server.previous)
        elif event.keyval == const.KEY_RIGHT:
            self.execute(self.server.next)
        elif event.keyval == const.KEY_VOLUME_UP:
            val = min(100, int(self.__volume.get_level()) + const.VOLUME_STEP)
            ui.set_banner("Volume set to %d" % val)
            self.execute(self.server.set_volume, val)
        elif event.keyval == const.KEY_VOLUME_DOWN:
            val = max(0, int(self.__volume.get_level()) - const.VOLUME_STEP)
            self.execute(self.server.set_volume, val)
            ui.set_banner("Volume set to %d" % val)
        else: return False

    def ui_disconnected(self, ui = None):
        self.__volume.set_sensitive(False)
        self.__volume.disconnect(self.__vsig)
        self.__volume.set_level(0)
        self.__vsig, self.__timeout = None, None

    def ui_connected(self, ui, status):
        if self.__vsig: self.ui_disconnected()
        self.__volume.set_sensitive(True)
        self.__volume.set_level(int(status["volume"]))
        self.__vsig = self.__volume.connect("level_changed",self.set_volume)

    def update_status(self, ui, status):
        if int(self.__volume.get_level()) != status["volume"]:
            # we need to update volume bar without send a signal
            self.__volume.handler_block(self.__vsig)
            self.__volume.set_level(status["volume"])
            self.__volume.handler_unblock(self.__vsig)

    def show_volumebar(self, widget):
        if self.__timeout:
            gobject.source_remove(self.__timeout)
        self.__volume.show()
        self.__controls.hide()
        self.__timeout = gobject.timeout_add(const.SHOW_TIMEOUT,\
            self.hide_volumebar)

    def hide_volumebar(self):
        self.__volume.hide()
        self.__controls.show()
        self.__timeout = None
        return False

    def set_volume(self, widget):
        if self.__timeout:
            gobject.source_remove(self.__timeout)
            self.__timeout = gobject.timeout_add(const.SHOW_TIMEOUT,\
                self.hide_volumebar)
        self.execute(self.server.set_volume, int(self.__volume.get_level()))

    def volume_mute_toggle(self, widget):
        pass

    def post_show_action(self, ui = None):
        self.__volume.hide()


class ControlsPanel(gtk.VBox):

    def __init__(self, ui):
        gtk.VBox.__init__(self)

        # we need it to update play/pause status
        self.__play_pause = PlayPauseButton()
        buttons = [PreviousButton(), self.__play_pause, StopButton(),\
                   NextButton()]

        for button in buttons:
            button.connect("clicked", button.action, ui.get_server())
            self.pack_start(button)

        # Signals
        ui.connect("update-status",self.update_status)
        ui.connect("connected",self.ui_connected)
        ui.connect("disconnected",self.ui_disconnected)

    def ui_disconnected(self, ui):
        for button in self.get_children():
            button.set_sensitive(False)
        self.__play_pause.set_play("stop")

    def ui_connected(self, ui, status):
        for button in self.get_children():
            button.set_sensitive(True)
        self.__play_pause.set_play(status["state"])

    def update_status(self, ui, status):
        self.__play_pause.set_play(status["state"])


#
# Controls Buttons
#

SIZE = gtk.icon_size_register("djmote-control", 72, 72)

class ControlButton(DjmoteButton, _BaseWidget):

    def __init__(self, sensitive = False):
        DjmoteButton.__init__(self)
        self.set_focus_on_click(False)
        self.has_focus = False
        self.set_sensitive(sensitive)

        self.img = gtk.image_new_from_stock(self.__class__.stock_img,SIZE)
        self.set_image(self.img)

    def action(self, widget, server):
        pass

class PlayPauseButton(ControlButton):
    stock_img = stock.DJMOTE_PLAY

    def set_play(self, player_state):
        """Update the play/pause button to have the correct image."""
        if player_state == "play":
            stock_img = stock.DJMOTE_PAUSE
        else:
            stock_img = stock.DJMOTE_PLAY
        self.img.set_from_stock(stock_img,SIZE)
        self.set_image(self.img)

    def action(self, widget, server):
        self.execute(server.play_toggle)

class NextButton(ControlButton):
    stock_img = stock.DJMOTE_NEXT

    def action(self, widget, server):
        self.execute(server.next)

class PreviousButton(ControlButton):
    stock_img = stock.DJMOTE_PREVIOUS

    def action(self, widget, server):
        self.execute(server.previous)

class StopButton(ControlButton):
    stock_img = stock.DJMOTE_STOP

    def action(self, widget, server):
        self.execute(server.stop)


class VolumeButton(ControlButton):
    stock_img = stock.DJMOTE_VOLUME


# vim: ts=4 sw=4 expandtab
