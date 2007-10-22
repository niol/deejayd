import gtk,hildon
from djmote import stock

class StatusBox(gtk.HBox):

    def __init__(self,player):
        gtk.HBox.__init__(self)

        self.toolbar = ToolBar(player)
        self.pack_start(self.toolbar)


class ToolBar(gtk.Toolbar):

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
        sep.set_expand(True)
        sep.set_draw(False)
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
