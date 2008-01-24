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

class ConnectDialog(gtk.Dialog):

    def __init__(self, parent, conf, connect_cb):
        gtk.Dialog.__init__(self, "Connect...", parent,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)

        self.conf = conf
        self.connect_cb = connect_cb

        layout = gtk.Table(rows=3, columns=2)

        host_label = gtk.Label('Host')
        layout.attach(host_label, 0, 1, 0, 1)
        self.host_entry = gtk.Entry(max=30)
        self.host_entry.set_text(self.conf['host'])
        layout.attach(self.host_entry, 1, 2, 0, 1)

        port_label = gtk.Label('Port')
        layout.attach(port_label, 0, 1, 1, 2)
        self.port_entry = gtk.Entry(max=5)
        self.port_entry.set_text(str(self.conf['port']))
        layout.attach(self.port_entry, 1, 2, 1, 2)

        startup_connect = gtk.CheckButton("Remember and connect on startup")
        startup_connect.connect("toggled", self.startup_connect_toggle)
        startup_connect.set_active(self.conf['connect_on_startup'])
        layout.attach(startup_connect, 0, 2, 2, 3)

        layout.show_all()
        self.vbox.pack_start(layout)

        cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancel_button.connect("clicked", lambda w: self.hide())
        self.action_area.pack_end(cancel_button)

        self.connect_button = gtk.Button('Connect')
        self.connect_button.connect("clicked", self.connect_now)
        self.action_area.pack_end(self.connect_button)

        self.action_area.show_all()

    def startup_connect_toggle(self, checkbutton, data=None):
        self.conf['connect_on_startup'] = checkbutton.get_active()

    def connect_now(self, widget, data=None):
        self.conf['host'] = self.host_entry.get_text()
        self.conf['port'] = int(self.port_entry.get_text())
        if self.conf['connect_on_startup']:
            self.conf.save()
        self.connect_cb(None, self.conf)
        self.hide()


class ErrorDialog(gtk.Dialog):

    def __init__(self, parent, error):
        gtk.Dialog.__init__(self, "Error", parent,\
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,\
                            (gtk.STOCK_OK, gtk.RESPONSE_OK,)
                            )
        label = gtk.Label(error)
        self.vbox.pack_start(label)
        self.connect("response", lambda a,b: self.destroy())
        self.show_all()

# vim: ts=4 sw=4 expandtab
