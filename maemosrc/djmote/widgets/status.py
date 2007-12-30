import gobject,gtk,hildon,pango
from djmote import stock

class StatusBox(gtk.HBox):

    def __init__(self,player):
        gtk.HBox.__init__(self)

        # toolbar
        toolbar = Toolbar(player)
        self.pack_start(toolbar)
        # current media
        self.pack_start(Current(player))

class Current(gtk.HBox):

    def __init__(self,player):
        gtk.HBox.__init__(self)
        self.__player = player
        player.connect("connected", self.update_status)
        player.connect("update-status", self.update_status)
        player.connect("disconnected", self.cb_disable)

        # name of current song
        self.__label = gtk.Label("")
        self.__label.set_line_wrap(True)
        self.__label.modify_font(pango.FontDescription("Sans Italic 13"))
        self.__label.set_justify(gtk.JUSTIFY_CENTER)
        self.__label.set_size_request(250,50)
        self.pack_start(self.__label, fill = False)
        # seekbar
        self.__seekbar = Seekbar(player)
        self.pack_start(self.__seekbar)
        # time button
        self.__time_button = gtk.Button(label = "0/0")
        self.__time_button.connect("clicked",self.__toggle_display)
        self.pack_start(self.__time_button, expand = False, fill = False)

        self.connect("show",self.post_show_action)

    def post_show_action(self, ui = None):
        self.__seekbar.hide()

    def update_status(self, ui, status):
        if status["state"] != "stop":
            server = ui.get_server()
            server.get_current().add_callback(self.cb_update_current)
            # update time
            times = status["time"].split(":")
            self.__time_button.set_label("%s/%s" % (times[0],times[1]))
            self.__time_button.set_sensitive(True)
            # update seekbar
            self.__seekbar.update_time(int(times[0]),int(times[1]))
        else:
            self.cb_disable()

    def cb_update_current(self, current):
        # update media title
        media = current.get_medias()[0]
        if media["type"] == "song":
            title = "%s (%s)" % (media["title"], media["artist"])
        else:
            title = media["title"]
        self.__label.set_text(title)

    def cb_disable(self):
        self.__label.set_text("No playing media")
        self.__time_button.set_label("0/0")
        self.__seekbar.disable_seekbar()

    def __toggle_display(self, widget):
        if self.__label.get_property("visible") == True:
            self.__label.hide()
            self.__seekbar.show_all()
        else:
            self.__label.show_all()
            self.__seekbar.hide()

class Seekbar(hildon.Seekbar):

    def __init__(self, player):
        hildon.Seekbar.__init__(self)
        self.set_size_request(250,50)
        self.__action = None

        self.set_sensitive(False)
        self.__signal = self.connect_after("change-value", self.cb_seek_to,\
                player)
        self.show()

    def update_time(self, current_time, total_time):
        self.set_sensitive(True)
        self.handler_block(self.__signal)
        self.set_total_time(total_time)
        self.set_fraction(total_time)
        self.set_position(current_time)
        self.handler_unblock(self.__signal)

    def disable_seekbar(self):
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
