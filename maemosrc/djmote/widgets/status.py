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

import gobject,gtk,hildon,pango
from djmote import stock
from djmote.const import SHOW_TIMEOUT
from deejayd.net.client import DeejaydError
from djmote.utils.decorators import gui_callback
from djmote.widgets._base import _BaseWidget, format_time

class StatusBox(_BaseWidget):
    # toolbar
    __sigs = {}
    __btns = {}

    def __init__(self, ui):
        self._signals = [ ("player.current", "update_media") ]
        self._signal_ids = []
        self.widget = gtk.HBox()

        self.server = ui.get_server()
        self.__timeout = None

        # toolbar
        toolbar = gtk.Toolbar()
        quit = gtk.ToggleToolButton(gtk.STOCK_QUIT)
        quit.connect("clicked",ui.destroy)
        toolbar.insert(quit, 0)
        # separator
        sep = gtk.SeparatorToolItem()
        sep.set_draw(True)
        toolbar.insert(sep, 1)
        options = {"random":stock.DJMOTE_SHUFFLE,"repeat": stock.DJMOTE_REPEAT}
        i = 2
        for opt in options.keys():
            self.__btns[opt] = gtk.ToggleToolButton(options[opt])
            self.__btns[opt].set_sensitive(False)
            self.__sigs[opt] = self.__btns[opt].connect("clicked",\
                self.set_option,opt)
            toolbar.insert(self.__btns[opt],i)
            i += 1
        self.widget.pack_start(toolbar)

        # current media
        current = gtk.HBox()
        # name of current song
        self.__curlabel = gtk.Label("")
        self.__curlabel.set_name("djmote-title")
        self.__curlabel.set_line_wrap(True)
        self.__curlabel.set_justify(gtk.JUSTIFY_CENTER)
        self.__curlabel.set_size_request(250,50)
        current.pack_start(self.__curlabel, fill = False)
        # seekbar
        self.__action = None
        self.__seekbar = hildon.Seekbar()
        self.__seekbar.set_size_request(250,50)
        self.__seekbar.set_sensitive(False)
        self.__sigs["seekbar"] = self.__seekbar.connect_after("change-value",\
            self.set_position)
        current.pack_start(self.__seekbar)
        self.widget.pack_start(current)

        # time button
        self.__time_button = gtk.Button("0:00/0:00")
        self.__time_button.connect("clicked",self.show_seekbar)
        self.widget.pack_start(self.__time_button, expand=False, fill=False)

        self.widget.connect("show",self.post_show_action)
        ui.connect("update-status",self.update_status)
        ui.connect("connected",self.ui_connected)
        ui.connect("disconnected",self.ui_disconnected)

    def ui_connected(self, ui, status):
        gobject.idle_add(self.subscribe)
        for btn in self.__btns.values():
            btn.set_sensitive(True)
        self.update_media(False)
        self.update_status(ui, status)

    def ui_disconnected(self, ui):
        self._signal_ids = []
        self.__reset_current()
        for btn in self.__btns.values():
            btn.set_sensitive(False)

    def update_status(self, ui, status):
        if status["state"] != "stop": self.__update_current_status(status)
        else: self.__reset_current()

        for (opt, btn) in self.__btns.items():
            value = btn.get_active() and 1 or 0
            if status[opt] != value:
                # Block signal
                btn.handler_block(self.__sigs[opt])
                new_v = not btn.get_active()
                btn.set_active(new_v)
                # Unblock signal
                btn.handler_unblock(self.__sigs[opt])

    def post_show_action(self, ui = None):
        self.__seekbar.hide()

    def set_option(self, widget, opt):
        value = self.__btns[opt].get_active() and 1 or 0
        self.execute(self.server.set_option, opt, value)

    def hide_seekbar(self):
        self.__curlabel.show_all()
        self.__seekbar.hide()

    def show_seekbar(self, widget):
        if self.__timeout:
            gobject.source_remove(self.__timeout)
        self.__curlabel.hide()
        self.__seekbar.show_all()
        self.__timeout = gobject.timeout_add(SHOW_TIMEOUT, self.hide_seekbar)

    def set_position(self, widget, scroll, value):
        def cb_timeout_seek(pos):
            self.execute(self.server.seek, pos)
            self.__action = None
            return False

        if self.__timeout:
            gobject.source_remove(self.__timeout)
            self.__timeout = gobject.timeout_add(SHOW_TIMEOUT,self.hide_seekbar)
        pos = self.__seekbar.get_position()
        if scroll in (gtk.SCROLL_PAGE_FORWARD,gtk.SCROLL_PAGE_BACKWARD):
            self.execute(self.server.seek, pos)
        elif scroll == gtk.SCROLL_JUMP:
            if self.__action != None: gobject.source_remove(self.__action)
            self.__action = gobject.timeout_add(250,cb_timeout_seek,pos)

    def update_media(self, reset_time = True):
        @gui_callback
        def cb_update_media(current):
            # update media title
            try: media = current.get_medias()[0]
            except (DeejaydError, IndexError, TypeError):
                self.__reset_current()
                return
            title = media["title"]
            if media["type"] == "song":
                title += " (%s)" % media["artist"]
            self.__curlabel.set_text(title)
            if reset_time:
                try: length = int(media["length"])
                except (KeyError, TypeError):
                    length = 0
                self.__update_seekbar(0, length)
        self.server.get_current().add_callback(cb_update_media)

    #
    # internal function
    #
    def __update_current_status(self, status):
        # update time
        times = status["time"].split(":")
        self.__time_button.set_label("%s/%s" %\
             (format_time(int(times[0])),format_time(int(times[1]))))
        self.__time_button.set_sensitive(True)
        # update seekbar
        self.__update_seekbar(int(times[0]), int(times[1]))

    def __reset_current(self):
        self.__curlabel.set_text("No playing media")
        self.__time_button.set_label("0:00/0:00")
        self.__update_seekbar(0, 0)

    def __update_seekbar(self, current, total):
        sens = True
        if total == 0:
            sens = False
        self.__seekbar.set_sensitive(sens)
        self.__seekbar.handler_block(self.__sigs["seekbar"])
        self.__seekbar.set_total_time(total)
        self.__seekbar.set_fraction(total)
        self.__seekbar.set_position(current);
        self.__seekbar.handler_unblock(self.__sigs["seekbar"])

# vim: ts=4 sw=4 expandtab
