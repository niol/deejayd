import os

import gtk,gobject
# Initializing GTK thread engine, as UI callbacks of deejayd command will be
# called from another thread.
# Thanks http://aruiz.typepad.com/siliconisland/2006/04/threads_on_pygt.html !
gtk.gdk.threads_init()

import hildon

from deejayd.net.client import DeejayDaemonAsync, DeejaydError, ConnectError
from djmote.conf import Config
from djmote import stock
from djmote.widgets.controls import ControlBox
from djmote.widgets.status import StatusBox
from djmote.widgets.mode import ModeBox
from djmote.widgets.dialogs import *
from djmote.utils.decorators import gui_callback

class DjmoteUI(hildon.Program):

    __gsignals__ = {
        'update-status':(gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE,(object,)),
        }

    def __init__(self):
        hildon.Program.__init__(self)
        self.__deejayd = DeejayDaemonAsync()

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
        self.add_window(self.main_window)

        # Connect window
        self.connect_window = ConnectDialog(self.main_window,
                                            self.__conf,
                                            self.connect_to_server)

        # Menu
        menu = DjmoteMenu(self)
        self.set_common_menu(menu)

        # Layout
        main_box = gtk.HBox()
        self.main_window.add(main_box)

        # controls
        main_box.pack_end(ControlBox(self), expand=False, fill=False)

        left_box = gtk.VBox(spacing = 5)
        main_box.pack_end(left_box)
        # status
        left_box.pack_start(StatusBox(self), expand = False,\
                            fill = False)

        # mode
        left_box.pack_start(ModeBox(self))

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
        try: self.__deejayd.connect(data['host'], data['port'])
        except ConnectError, msg:
            self.set_error(msg)
        else:
            # get player status
            self.__deejayd.get_status().add_callback(self.cb_get_status)

    def show_connect_window(self, widget=None):
        self.connect_window.show()

    # Player Commands
    def update_ui(self, widget = None, data = None):
        self.__deejayd.get_status().add_callback(self.cb_get_status)

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

    def set_video_dir(self,dir):
        self.__deejayd.set_video_dir(dir).add_callback(self.cb_update_status)

    def set_option(self,option_name,option_value):
        self.__deejayd.set_option(option_name,option_value).add_callback(\
                                                        self.cb_update_status)

    def set_mode(self, mode):
        self.__deejayd.set_mode(mode).add_callback(self.cb_update_status)

    def set_error(self, error):
        ErrorDialog(self.main_window, error)

    @gui_callback
    def cb_update_status(self, answer):
        try: contents = answer.get_contents()
        except DeejaydError, err: self.set_error(err)
        else:
            if contents:
                self.update_ui()
            else: self.set_error("Unknown Error")

    @gui_callback
    def cb_get_status(self, answer):
        try: answer.get_contents()
        except DeejaydError, err: self.set_error(err)
        else:
            self.emit("update-status",answer)


class DjmoteMenu(gtk.Menu):

    def __init__(self, player):
        gtk.Menu.__init__(self)
        self.__player = player
        self.__mode_menu = None

        # build menu
        menu_connect = gtk.MenuItem("Connect...")
        menu_connect.connect("activate", self.__player.show_connect_window)
        self.append(menu_connect)
        menu_connect.show()

        menu_quit = gtk.MenuItem("Quit")
        menu_quit.connect("activate", self.__player.destroy)
        self.append(menu_quit)
        menu_quit.show()

        self.__player.connect("update-status", self.update_mode_menu)

    def update_mode_menu(self, ui, status):
        mode = status["mode"]

        if self.__mode_menu == None:
            self.__mode_menu = {"current": mode, "items":{}, \
                "signals": {}}
            server = self.__player.get_server()
            server.get_mode().add_callback(self.cb_build_mode_menu)

        elif self.__mode_menu["current"] != mode:
            self.__mode_menu["current"] = mode
            self.__mode_menu["items"][mode].handler_block(\
                self.__mode_menu["signals"][mode])
            self.__mode_menu["items"][mode].activate()
            self.__mode_menu["items"][mode].handler_unblock(\
                self.__mode_menu["signals"][mode])

    def set_mode(self, menuitem, mode):
        self.__mode_menu["current"] = mode
        self.__player.set_mode(mode)

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

        mode_menu = gtk.MenuItem("Mode")
        mode_menu.set_submenu(sub_menu)

        self.insert(mode_menu, 1)
        mode_menu.show_all()

# vim: ts=4 sw=4 expandtab
