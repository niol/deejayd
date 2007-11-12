import os

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
from djmote.widgets.dialogs import *
from djmote.utils.decorators import gui_callback

osso_c = osso.Context("djmote", "0.1.0", False)

class DjmoteUI(hildon.Program):

    global osso_c
    __gsignals__ = {
        'update-status':(gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE,(object,)),
        'connected':(gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE,(object,)),
        'disconnected':(gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE,()),
        }

    def __init__(self):
        hildon.Program.__init__(self)
        self.__deejayd = DeejayDaemonAsync()
        self.volume = 0

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
        self.main_window.connect("key-press-event", self.key_press)
        self.add_window(self.main_window)
        self.__fullscreen = False

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
        left_box.pack_start(StatusBox(self), expand = False, fill = False)

        # mode
        left_box.pack_start(ModeBox(self))

    def run(self):
        self.main_window.show_all()

        # DBUS initialisation
        from djmote.utils import maemo
        maemo.init(self)

        if not self.__conf['connect_on_startup']:
            self.show_connect_window()
        else:
            self.connect_to_server(None, self.__conf)

        gtk.gdk.threads_enter()
        gtk.main()
        gtk.gdk.threads_leave()

    def destroy(self, widget, data=None):
        self.__deejayd.disconnect()
        gtk.main_quit()

    def key_press(self, widget, event):
        if not self.__deejayd.is_connected(): return False

        if event.keyval == const.KEY_ENTER:
            self.play_toggle()
        elif event.keyval == const.KEY_LEFT:
            self.previous()
        elif event.keyval == const.KEY_RIGHT:
            self.next()
        elif event.keyval == const.KEY_FULLSCREEN:
            if self.__fullscreen:
                self.main_window.unfullscreen()
                self.__fullscreen = False
            else:
                self.main_window.fullscreen()
                self.__fullscreen = True
        elif event.keyval == const.KEY_VOLUME_UP:
            val = self.volume + const.VOLUME_STEP
            self.set_banner("increase volume to %d" % val)
            self.__deejayd.set_volume(val).add_callback(self.cb_update_status)
        elif event.keyval == const.KEY_VOLUME_DOWN:
            val = self.volume - const.VOLUME_STEP
            self.set_banner("decrease volume to %d" % val)
            self.__deejayd.set_volume(val).add_callback(self.cb_update_status)
        else: return False
        return True

    def is_connected(self):
        return self.__deejayd.is_connected()

    def connect_to_server(self, widget, data):
        if self.is_connected(): self.disconnect_to_server()
        try: self.__deejayd.connect(data['host'], data['port'])
        except ConnectError, msg:
            self.set_error(msg)
        else:
            @gui_callback
            def cb_connect_status(answer):
                try: answer.get_contents()
                except DeejaydError, err: self.set_error(err)
                else:
                    # record volume
                    self.volume = answer["volume"]
                    self.emit('connected', answer)

            # get player status
            self.__deejayd.get_status().add_callback(cb_connect_status)

    def disconnect_to_server(self, widget = None, data = None):
        if not self.is_connected(): return
        self.__deejayd.disconnect()
        self.emit('disconnected')

    def show_connect_window(self, widget=None):
        self.connect_window.show()

    def set_banner(self, msg):
        note = osso.SystemNote(osso_c)
        note.system_note_infoprint(msg)

    # Player Commands
    def update_ui(self, widget = None, data = None):
        self.__deejayd.get_status().add_callback(self.cb_get_status)

    def play_toggle(self, widget = None, data = None):
        self.__deejayd.play_toggle().add_callback(self.cb_update_status)

    def go_to(self, id):
        self.__deejayd.go_to(id).add_callback(self.cb_update_status)

    def stop(self, widget = None, data = None):
        self.__deejayd.stop().add_callback(self.cb_update_status)

    def next(self, widget = None, data = None):
        self.__deejayd.next().add_callback(self.cb_update_status)

    def previous(self, widget = None, data = None):
        self.__deejayd.previous().add_callback(self.cb_update_status)

    def seek(self, pos):
        self.__deejayd.seek(pos).add_callback(self.cb_update_status)

    def set_volume(self, volume):
        self.__deejayd.set_volume(volume).add_callback(self.cb_update_status)

    def set_video_dir(self,dir):
        self.__deejayd.set_video_dir(dir).add_callback(self.cb_update_status)

    def set_option(self,option_name,option_value):
        self.__deejayd.set_option(option_name,option_value).add_callback(\
                                                        self.cb_update_status)

    def set_mode(self, mode):
        self.__deejayd.set_mode(mode).add_callback(self.cb_update_status)

    def dvd_reload(self, widget, data = None):
        self.__deejayd.dvd_reload().add_callback(self.cb_update_status)

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
            # record volume
            try: self.volume = answer["volume"]
            except TypeError: self.set_error("Strange, unable to get status")
            else:
                self.emit("update-status",answer)


class DjmoteMenu(gtk.Menu):

    def __init__(self, player):
        gtk.Menu.__init__(self)
        self.__player = player
        self.__mode_menu = None
        self.mode_menu = None

        # build menu
        menu_connect = gtk.MenuItem("Connect...")
        menu_connect.connect("activate", self.__player.show_connect_window)
        self.append(menu_connect)

        menu_disconnect = gtk.MenuItem("Disconnect...")
        menu_disconnect.connect("activate", self.__player.disconnect_to_server)
        self.append(menu_disconnect)

        menu_quit = gtk.MenuItem("Quit")
        menu_quit.connect("activate", self.__player.destroy)
        self.append(menu_quit)

        # Signals
        self.__player.connect("connected", self.build_mode_menu)
        self.__player.connect("disconnected", self.erase_mode_menu)
        self.__player.connect("update-status", self.update_mode_menu)
        self.show_all()

    def build_mode_menu(self, ui, status):
        mode = status["mode"]
        self.__mode_menu = {"current": mode, "items":{}, \
            "signals": {}}
        server = self.__player.get_server()
        server.get_mode().add_callback(self.cb_build_mode_menu)

    def erase_mode_menu(self, ui):
        self.__mode_menu = None
        # remove mode submenu
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

        self.mode_menu = gtk.MenuItem("Mode")
        self.mode_menu.set_submenu(sub_menu)

        self.insert(self.mode_menu, 1)
        self.mode_menu.show_all()

# vim: ts=4 sw=4 expandtab
