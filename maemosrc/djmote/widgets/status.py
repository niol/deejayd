import gobject,gtk,hildon
from djmote import stock

class StatusBox(gtk.HBox):

    def __init__(self,player):
        gtk.HBox.__init__(self)

        self.pack_start(Toolbar(player))
        self.pack_start(Seekbar(player))


class Seekbar(hildon.Seekbar):

    def __init__(self, player):
        hildon.Seekbar.__init__(self)
        self.__action = None

        player.connect("connected", self.update_status)
        player.connect("disconnected", self.disable_seekbar)
        player.connect("update-status", self.update_status)

        self.set_sensitive(False)
        self.__signal = self.connect_after("change-value", self.cb_seek_to,\
                player)
        self.show()

    def update_status(self, ui, status):
        if status["state"] == "stop": self.disable_seekbar()
        else:
            self.set_sensitive(True)
            times = status["time"].split(":")
            self.handler_block(self.__signal)
            self.set_total_time(int(times[1]))
            self.set_fraction(int(times[1]))
            self.set_position(int(times[0]))
            self.handler_unblock(self.__signal)

    def disable_seekbar(self, ui = None):
        self.set_sensitive(False)
        self.handler_block(self.__signal)
        self.set_position(0);
        self.set_fraction(0)
        self.handler_unblock(self.__signal)

    def cb_seek_to(self, widget, scroll, value, player):
        pos = self.get_position()
        if scroll in (gtk.SCROLL_PAGE_FORWARD,gtk.SCROLL_PAGE_BACKWARD):
            player.seek(pos)
        elif scroll == gtk.SCROLL_JUMP:
            if self.__action != None: gobject.source_remove(self.__action)
            self.__action = gobject.timeout_add(250,self.cb_timeout_seek,\
                                player,pos)

    def cb_timeout_seek(self,player,pos):
        player.seek(pos)
        self.__action = None


class Toolbar(gtk.Toolbar):

    def __init__(self,player):
        gtk.Toolbar.__init__(self)
        self.__player = player
        self.__contents = {}
        self.__signals = {}

        # build toolbar
        options = {"random":stock.DJMOTE_SHUFFLE,"repeat": stock.DJMOTE_REPEAT}
        i = 0
        for opt in options.keys():
            self.__contents[opt] = gtk.ToggleToolButton(options[opt])
            self.__contents[opt].set_sensitive(False)
            self.__signals[opt] = self.__contents[opt].connect("clicked",\
                                    self.set_option,opt)
            self.insert(self.__contents[opt],i)
            i += 1

        # separator
        sep = gtk.SeparatorToolItem()
        sep.set_draw(True)
        self.insert(sep,2)

        refresh = gtk.ToolButton(gtk.STOCK_REFRESH)
        refresh.set_sensitive(False)
        refresh.connect("clicked",self.__player.update_ui)
        self.insert(refresh,3)

        # signals
        player.connect("update-status", self.update_status)
        player.connect("connected", self.ui_connected)
        player.connect("disconnected", self.ui_disconnected)

    def ui_connected(self, ui, status):
        for i in range(self.get_n_items()):
            button = self.get_nth_item(i)
            button.set_sensitive(True)
        self.update_status(ui, status)

    def ui_disconnected(self, ui):
        for i in range(self.get_n_items()):
            button = self.get_nth_item(i)
            button.set_sensitive(False)

    def update_status(self, ui, status):
        for option in self.__contents.keys():
            value = self.__contents[option].get_active() and 1 or 0
            if status[option] != value:
                # Block signal
                self.__contents[option].handler_block(self.__signals[option])
                new_v = not self.__contents[option].get_active()
                self.__contents[option].set_active(new_v)
                # Unblock signal
                self.__contents[option].handler_unblock(self.__signals[option])

    def set_option(self,widget,data):
        value = self.__contents[data].get_active() and 1 or 0
        self.__player.set_option(data,value)

# vim: ts=4 sw=4 expandtab
