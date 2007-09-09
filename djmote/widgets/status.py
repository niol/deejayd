import gtk,hildon
from djmote import stock

class StatusBox(gtk.HBox):

    def __init__(self,player):
        gtk.HBox.__init__(self)

        self.toolbar = ToolBar(player)
        self.pack_start(self.toolbar)

    def update_status(self,status):
        self.toolbar.update_status(status)

    def post_show_action(self): pass


class ToolBar(gtk.Toolbar):

    def __init__(self,player):
        gtk.Toolbar.__init__(self)
        self.__player = player
        self.__contents = {}

        # build toolbar
        self.__contents["random"] = gtk.ToggleToolButton(stock.DJMOTE_SHUFFLE)
        self.__contents["random"].connect("clicked",self.set_option,"random")
        self.insert(self.__contents["random"],0)

        self.__contents["repeat"] = gtk.ToggleToolButton(stock.DJMOTE_REPEAT)
        self.__contents["repeat"].connect("clicked",self.set_option,"repeat")
        self.insert(self.__contents["repeat"],1)

        self.__contents["fullscreen"] = gtk.ToggleToolButton(\
                                                        gtk.STOCK_DND)
        self.__contents["fullscreen"].connect("clicked",self.set_option,\
                                                        "fullscreen")
        self.insert(self.__contents["fullscreen"],2)

    def update_status(self,status): 
        for option in self.__contents.keys():
            value = self.__contents[option].get_active() and 1 or 0
            if status[option] != value:
                new_v = not self.__contents[option].get_active()
                self.__contents[option].set_active(new_v)

    def set_option(self,widget,data):
        value = self.__contents[data].get_active() and 1 or 0
        self.__player.set_option(data,value)

# vim: ts=4 sw=4 expandtab
