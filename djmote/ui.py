import os

import gtk,gobject
# Initializing GTK thread engine, as UI callbacks of deejayd command will be
# called from another thread.
# Thanks http://aruiz.typepad.com/siliconisland/2006/04/threads_on_pygt.html !
gtk.gdk.threads_init()

import hildon

from deejayd.net.client import DeejayDaemonAsync
from djmote.conf import Config
from djmote import stock
from djmote.widgets.controls import ControlBox
from djmote.widgets.status import StatusBox
from djmote.widgets.mode import ModeBox
from djmote.widgets.dialogs import *
from djmote.utils.decorators import gui_callback

class DjmoteUI(hildon.Program):

    __gsignals__ = {
        'update-status':(gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (object,)),
        }

    def __init__(self):
        hildon.Program.__init__(self)
        self.app = hildon.Program()
        self.__deejayd = DeejayDaemonAsync()
        self.__widgets = {}

        # Conf
        conffile = os.path.expanduser('~/.djmoterc')
        self.__conf = Config(conffile)

        # Custom Icons
        stock.init()

    def get_server(self):
        return self.__deejayd

    def build(self):
        self.main_window = hildon.Window()
        self.main_window.connect("destroy", self.destroy)
        self.app.add_window(self.main_window)

        # Connect window
        self.connect_window = ConnectDialog(self.main_window,
                                            self.__conf,
                                            self.connect_to_server)

        # Menu
        menu = gtk.Menu()

        menu_connect = gtk.MenuItem("Connect...")
        menu_connect.connect("activate", self.show_connect_window)
        menu.append(menu_connect)
        menu_connect.show()

        menu_quit = gtk.MenuItem("Quit")
        menu_quit.connect("activate", self.destroy)
        menu.append(menu_quit)
        menu_quit.show()

        self.main_window.set_menu(menu)

        # Layout
        main_box = gtk.HBox()
        self.main_window.add(main_box)

        # controls
        self.__widgets['controls'] = ControlBox(self)
        main_box.pack_end(self.__widgets['controls'], expand=False, fill=False)

        left_box = gtk.VBox(spacing = 5)
        main_box.pack_end(left_box)
        # status
        self.__widgets['status'] = StatusBox(self)
        left_box.pack_start(self.__widgets['status'], expand = False,\
                            fill = False)

        # mode
        self.__widgets['mode'] = ModeBox(self)
        left_box.pack_start(self.__widgets['mode'])

    def run(self):
        self.main_window.show_all()
        if not self.__conf['connect_on_startup']:
            self.show_connect_window()
        else:
            self.connect_to_server(None, self.__conf)
        gtk.main()

    def destroy(self, widget, data=None):
        self.__deejayd.disconnect()
        gtk.main_quit()

    def connect_to_server(self, widget, data):
        self.__deejayd.connect(data['host'], data['port'])
        self.__deejayd.get_status().add_callback(self.cb_get_status)

    def show_connect_window(self, widget=None):
        self.connect_window.show()

    # Player Controls
    def play_toggle(self, widget, data = None):
        self.__deejayd.play_toggle().add_callback(self.cb_update_status)

    def go_to(self, id):
        self.__deejayd.go_to(id).add_callback(self.cb_update_status)

    def stop(self, widget, data = None):
        self.__deejayd.stop().add_callback(self.cb_update_status)

    def next(self, widget, data = None):
        self.__deejayd.next().add_callback(self.cb_update_status)

    def previous(self, widget, data = None):
        self.__deejayd.previous().add_callback(self.cb_update_status)

    def set_volume(self, volume):
        self.__deejayd.set_volume(volume).add_callback(self.cb_update_status)

    def set_option(self,option_name,option_value):
        self.__deejayd.set_option(option_name,option_value).add_callback(\
                                                        self.cb_update_status)

    @gui_callback
    def cb_update_status(self, answer):
        if answer.get_contents() == True:
            self.__deejayd.get_status().add_callback(self.cb_get_status)

    @gui_callback
    def cb_get_status(self, answer):
        self.emit("update-status",answer)

# vim: ts=4 sw=4 expandtab
