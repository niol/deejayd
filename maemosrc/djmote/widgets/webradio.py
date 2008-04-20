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
import gtk, gobject
from djmote.utils.decorators import gui_callback
from deejayd.net.client import DeejaydError
from djmote.widgets._base import _BaseSourceBox, _BaseWidget


class WebradioBox(_BaseSourceBox):
    _toolbar_items = [
        (gtk.STOCK_ADD, "add_dialog"),
        (gtk.STOCK_REMOVE, "remove_webradio"),
        (gtk.STOCK_CLEAR, "clear"),
        ]

    def __init__(self, player):
        self._signals = [ ("webradio.listupdate", "update") ]
        self._signal_ids = []
        self.source = player.get_webradios()
        _BaseSourceBox.__init__(self, player)

    def _format_text(self, m):
        return "%s\n\t<i>%s</i>" %\
            (gobject.markup_escape_text(m["title"]),\
             gobject.markup_escape_text(m["url"]))

    def remove_webradio(self, widget):
        ids = self.get_selection()
        if ids != []:
            self.set_loading()
            self.execute(self.source.delete_webradios, ids)

    def clear(self, widget):
        self.set_loading()
        self.execute(self.source.clear)

    def add_dialog(self, widget):
        AddDialog(self.source)


class AddDialog(gtk.Dialog,_BaseWidget):

    def __init__(self, webradio):
        self.source = webradio
        gtk.Dialog.__init__(self,"Add Webradio",None,\
            gtk.DIALOG_DESTROY_WITH_PARENT,
             (gtk.STOCK_ADD, gtk.RESPONSE_OK,\
              gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        layout = gtk.Table(rows=2, columns=2)

        name_label = gtk.Label('Name')
        layout.attach(name_label, 0, 1, 0, 1)
        self.name_entry = gtk.Entry(max=32)
        layout.attach(self.name_entry, 1, 2, 0, 1)

        url_label = gtk.Label('Url')
        layout.attach(url_label, 0, 1, 1, 2)
        self.url_entry = gtk.Entry(max=128)
        layout.attach(self.url_entry, 1, 2, 1, 2)

        self.vbox.pack_start(layout)
        self.connect("response", self.cb_response, webradio)
        self.show_all()

    def cb_response(self, dialog, response_id, webradio):
        if response_id == gtk.RESPONSE_CANCEL:
            self.destroy()
        elif response_id == gtk.RESPONSE_OK:
            name = self.name_entry.get_text()
            url = self.url_entry.get_text()
            if name != "" and url != "":
                self.source.add_webradio(name, url).\
                    add_callback(self.cb_add_webradio)

    @gui_callback
    def cb_add_webradio(self, answer):
        try: answer.get_contents()
        except DeejaydError, err:
            self.error(err)
        else:
            self.destroy()

# vim: ts=4 sw=4 expandtab
