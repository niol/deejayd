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

import os,thread

import gtk,gobject
# Initializing GTK thread engine, as UI callbacks of deejayd command will be
# called from another thread.
# Thanks http://aruiz.typepad.com/siliconisland/2006/04/threads_on_pygt.html !
gtk.gdk.threads_init()

import hildon, osso

from deejayd.net.client import DeejayDaemonAsync, DeejaydError, ConnectError
from djmote.conf import Config
from djmote import stock, const
from djmote.widgets.controls import ControlBox
from djmote.widgets.status import StatusBox
from djmote.widgets.mode import ModeBox
from djmote.widgets._base import _BaseWidget
from djmote.utils.decorators import gui_callback

osso_c = osso.Context("djmote", "0.1.0", False)

class DjmoteUI(hildon.Program, _BaseWidget):

    global osso_c
    __gsignals__ = {
        'update-status':(gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE,(object,)),
        'connected':(gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE,(object,)),
        'disconnected':(gobject.SIGNAL_RUN_FIRST,gobject.TYPE_NONE,()),
        }

    def __init__(self):
        hildon.Program.__init__(self)
        # parse custom rc file
        gtk.rc_parse(const.GTKRC_FILE)
        self.__deejayd = DeejayDaemonAsync()
        self.__deejayd.add_connect_callback(self.connect_callback)
        self.__deejayd.add_error_callback(self.error_callback)

        # Conf
        conffile = os.path.expanduser('~/.djmoterc')
        self.__conf = Config(conffile)

        # Custom Icons
        stock.init()

    def build(self):
        self.main_window = hildon.Window()
        self.main_window.connect("destroy", self.destroy)
        self.main_window.connect("key-press-event", self.key_press)
        self.add_window(self.main_window)
        self.__fullscreen = False

        # Menu
        menu = DjmoteMenu(self)
        self.set_common_menu(menu)

        # Layout
        main_box = gtk.VBox()
        self.main_window.add(main_box)

        # status
        main_box.pack_start(StatusBox(self).widget, expand=False, fill=False)

        bottom_box = gtk.HBox(spacing = 5)
        main_box.pack_end(bottom_box)
        # controls
        bottom_box.pack_end(ControlBox(self).widget, expand=False, fill=False)
        # mode
        bottom_box.pack_start(ModeBox(self))

    def get_server(self):
        return self.__deejayd

    def get_window(self):
        return self.main_window

    def run(self):
        self.main_window.show_all()

        # DBUS initialisation
        from djmote.utils import maemo
        thread.start_new_thread(maemo.init, (self,))

        if not self.__conf['connect_on_startup']:
            self.show_connect_window()
        else:
            self.connect_to_server(None, self.__conf)

        gtk.main()

    def destroy(self, widget, data=None):
        self.__deejayd.disconnect()
        gtk.main_quit()

    def key_press(self, widget, event):
        if not self.__deejayd.is_connected(): return False
        if event.keyval == const.KEY_FULLSCREEN:
            if self.__fullscreen:
                self.main_window.unfullscreen()
                self.__fullscreen = False
            else:
                self.main_window.fullscreen()
                self.__fullscreen = True
        else: return False

    def connect_to_server(self, widget, data):
        self.disconnect_to_server()
        self.__deejayd.connect(data['host'], data['port'])

    def disconnect_to_server(self, widget = None, data = None):
        if self.__deejayd.is_connected(): self.emit('disconnected')
        self.__deejayd.disconnect()

    def show_connect_window(self, widget=None):
        ConnectDialog(self.main_window, self.__conf, self.connect_to_server)

    def set_banner(self, msg):
        note = osso.SystemNote(osso_c)
        note.system_note_infoprint(msg)

    def update_ui(self, data = None):
        self.__deejayd.get_status().add_callback(self.cb_update_ui)

    @gui_callback
    def error_callback(self,msg):
        self.error(msg)
        self.emit('disconnected')

    @gui_callback
    def connect_callback(self, rs, msg):
        if rs == False: self.error(msg)
        else:
            gobject.idle_add(self.set_subscription)
            # get player status
            self.__deejayd.get_status().add_callback(self.cb_connect_status)

    @gui_callback
    def cb_connect_status(self,answer):
        try: status = answer.get_contents()
        except DeejaydError, err: self.error(err)
        else:
            self.emit('connected', status)

    @gui_callback
    def cb_update_ui(self, answer):
        try: status = answer.get_contents()
        except DeejaydError, err: self.error(err)
        else:
            self.emit("update-status",answer)

    def set_subscription(self):
        self.__sig_id = self.__deejayd.subscribe('player.status',self.update_ui)


class DjmoteMenu(gtk.Menu, _BaseWidget):

    def __init__(self, ui):
        gtk.Menu.__init__(self)
        self.server = ui.get_server()
        self.__mode_menu = None
        self.mode_menu = None
        self.refresh_menu = None

        # build menu
        menu_connect = gtk.MenuItem("Connect...")
        menu_connect.connect("activate", ui.show_connect_window)
        self.append(menu_connect)

        menu_disconnect = gtk.MenuItem("Disconnect...")
        menu_disconnect.connect("activate", ui.disconnect_to_server)
        self.append(menu_disconnect)

        menu_quit = gtk.MenuItem("Quit")
        menu_quit.connect("activate", ui.destroy)
        self.append(menu_quit)

        # Signals
        ui.connect("connected", self.connected)
        ui.connect("disconnected", self.disconnected)
        ui.connect("update-status", self.update_mode_menu)
        self.show_all()

    def connected(self, ui, status):
        if self.refresh_menu: self.refresh_menu.destroy()
        self.refresh_menu = gtk.MenuItem("Refresh")
        self.refresh_menu.connect("activate", ui.update_ui)
        self.insert(self.refresh_menu, 1)
        self.show_all()
        # list modes
        mode = status["mode"]
        self.__mode_menu = {"current": mode, "items":{}, "signals": {}}
        self.server.get_mode().add_callback(self.cb_build_mode_menu)

    def disconnected(self, ui):
        if self.refresh_menu:
            self.refresh_menu.destroy()
            self.refresh_menu = None
        # remove mode submenu
        self.__mode_menu = None
        if self.mode_menu:
            self.mode_menu.destroy()
            self.mode_menu = None

    def update_mode_menu(self, ui, status):
        mode = status["mode"]
        if self.__mode_menu["current"] != mode:
            self.__mode_menu["current"] = mode
            self.__mode_menu["items"][mode].handler_block(\
                self.__mode_menu["signals"][mode])
            self.__mode_menu["items"][mode].activate()
            self.__mode_menu["items"][mode].handler_unblock(\
                self.__mode_menu["signals"][mode])

    def set_mode(self, menuitem, mode):
        if menuitem.get_active():
            self.__mode_menu["current"] = mode
            self.execute(self.server.set_mode, mode)

    @gui_callback
    def cb_build_mode_menu(self, answer):
        radio_item = None
        sub_menu = gtk.Menu()

        modes = answer.get_contents()
        for mode in modes.keys():
            if modes[mode]:
                radio_item = gtk.RadioMenuItem(radio_item, mode)
                if mode == self.__mode_menu["current"]:
                    radio_item.activate()
                self.__mode_menu["signals"][mode] = radio_item.\
                    connect("activate", self.set_mode, mode)
                sub_menu.append(radio_item)
                self.__mode_menu["items"][mode] = radio_item

        self.mode_menu = gtk.MenuItem("Mode")
        self.mode_menu.set_submenu(sub_menu)

        self.insert(self.mode_menu, 1)
        self.mode_menu.show_all()


class ConnectDialog(gtk.Dialog):

    def __init__(self, parent, conf, connect_cb):
        gtk.Dialog.__init__(self, "Connect...", parent,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CONNECT,  gtk.RESPONSE_OK,\
                             gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

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

        self.vbox.pack_start(layout)
        self.connect("response", self.cb_response)
        self.show_all()

    def startup_connect_toggle(self, checkbutton, data=None):
        self.conf['connect_on_startup'] = checkbutton.get_active()

    def cb_response(self, dialog, response_id):
        if response_id == gtk.RESPONSE_OK:
            self.conf['host'] = self.host_entry.get_text()
            self.conf['port'] = int(self.port_entry.get_text())
            if self.conf['connect_on_startup']:
                self.conf.save()
            self.connect_cb(None, self.conf)
        self.destroy()

# vim: ts=4 sw=4 expandtab
