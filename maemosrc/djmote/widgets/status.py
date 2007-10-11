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
        self.__contents["random"] = gtk.ToggleToolButton(stock.DJMOTE_SHUFFLE)
        self.__signals["random"] = self.__contents["random"].connect("clicked",\
                                            self.set_option,"random")
        self.insert(self.__contents["random"],0)

        self.__contents["repeat"] = gtk.ToggleToolButton(stock.DJMOTE_REPEAT)
        self.__signals["repeat"] = self.__contents["repeat"].connect("clicked",\
                                            self.set_option,"repeat")
        self.insert(self.__contents["repeat"],1)

        self.__contents["fullscreen"] = gtk.ToggleToolButton(\
                                                        gtk.STOCK_DND)
        self.__signals["fullscreen"] = self.__contents["fullscreen"].\
                connect("clicked", self.set_option,"fullscreen")
        self.insert(self.__contents["fullscreen"],2)

        player.connect("update-status", self.update)

    def update(self, ui, status): 
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
