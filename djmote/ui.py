import os

import gtk
# Initializing GTK thread engine, as UI callbacks of deejayd command will be
# called from another thread.
# Thanks http://aruiz.typepad.com/siliconisland/2006/04/threads_on_pygt.html !
gtk.gdk.threads_init()

import hildon

from deejayd.net.client import DeejayDaemon
from djmote.conf import Config
from djmote import stock
from djmote.widgets import controls
from djmote.widgets.dialogs import *

# This is a decorator for our GUI callbacks : every GUI callback will be GTK
# thread safe that way.
def gui_callback(func):
    def gtk_thread_safe_func(*__args,**__kw):
        gtk.gdk.threads_enter()
        try:
            func(*__args, **__kw)
        finally:
            gtk.gdk.threads_leave()
    return gtk_thread_safe_func


class DjmoteUI(hildon.Program):

    def __init__(self):
        hildon.Program.__init__(self)
        self.app = hildon.Program()
        self.__deejayd = DeejayDaemon()
        self.__player_state = None

        # Conf
        conffile = os.path.expanduser('~/.djmoterc')
        self.__conf = Config(conffile)

        # Custom Icons
        stock.init()

    def build(self):
        self.main_window = hildon.Window()
        self.main_window.connect("destroy", self.destroy)
        self.app.add_window(self.main_window)

        # Connect window
        self.connect_window = ConnectDialog(self.main_window,
                                            self.__conf,
                                            self.connect)

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
        main_box = gtk.VBox()
        self.main_window.add(main_box)

        status_box = gtk.HBox()
        main_box.pack_start(status_box)

        bottom_box = gtk.HBox()
        main_box.pack_end(bottom_box)

        controls_box = gtk.VBox()
        bottom_box.pack_end(controls_box, fill=False)

        # Controls
        self.controls_button = controls.buttons
        for (name,action) in [("previous",self.previous),\
                              ("stop",self.stop),\
                              ("play-pause",self.play_toggle),\
                              ("next",self.next),]:
            self.controls_button[name].connect("clicked", action)
            controls_box.pack_end(self.controls_button[name])

    def run(self):
        self.main_window.show_all()
        if not self.__conf['connect_on_startup']:
            self.show_connect_window()
        else:
            self.connect(None, self.__conf)
        gtk.main()

    def destroy(self, widget, data=None):
        self.__deejayd.disconnect()
        gtk.main_quit()

    def connect(self, widget, data):
        self.__deejayd.connect(data['host'], data['port'])
        self.__deejayd.get_status().add_callback(self.cb_get_status)

    def show_connect_window(self, widget=None):
        self.connect_window.show()

    def play_toggle(self, widget, data = None):
        self.__deejayd.play_toggle().add_callback(self.cb_play_toggle)

    def stop(self, widget, data = None):
        self.__deejayd.stop().add_callback(self.cb_update_status)

    def next(self, widget, data = None):
        self.__deejayd.next().add_callback(self.cb_update_status)

    def previous(self, widget, data = None):
        self.__deejayd.previous().add_callback(self.cb_update_status)

    @gui_callback
    def cb_play_toggle(self, answer):
        if answer.get_contents() == True:
            if self.__player_state == "play":
                self.set_player_state("pause")
            else:
                self.set_player_state("play")

    @gui_callback
    def cb_update_status(self, answer):
        if answer.get_contents() == True:
            self.__deejayd.get_status().add_callback(self.cb_get_status)

    @gui_callback
    def cb_get_status(self, answer):
        self.set_player_state(answer['state'])

    def set_player_state(self, state):
        self.__player_state = state
        self.controls_button["play-pause"].set_play(self.__player_state)


# vim: ts=4 sw=4 expandtab