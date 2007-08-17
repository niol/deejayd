import gtk


class PlayPauseButton(gtk.Button):

    def __init__(self):
        gtk.Button.__init__(self)
        self.img = gtk.Image()

    def set_play(self, player_state):
        """Update the play/pause button to have the correct image."""
        if player_state == "play":
            pixbuf = self.img.render_icon(gtk.STOCK_MEDIA_PAUSE, 
                                          gtk.ICON_SIZE_LARGE_TOOLBAR)
            self.set_label("_Pause")
        else:
            pixbuf = self.img.render_icon(gtk.STOCK_MEDIA_PLAY, 
                                          gtk.ICON_SIZE_LARGE_TOOLBAR)
            self.set_label("_Play")
        self.img.set_from_pixbuf(pixbuf)
        self.set_image(self.img)


class ConnectDialog(gtk.Dialog):

    def __init__(self, parent, conf, connect_cb):
        gtk.Dialog.__init__(self, "Connect...", parent,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)

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
        startup_connect.connect("toggled", self.sartup_connect_toggle)
        startup_connect.set_active(self.conf['connect_on_startup'])
        layout.attach(startup_connect, 0, 2, 2, 3)

        layout.show_all()
        self.vbox.pack_start(layout)

        cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancel_button.connect("clicked", lambda w: self.hide())
        self.action_area.pack_end(cancel_button)

        self.connect_button = gtk.Button('Connect')
        self.connect_button.connect("clicked", self.connect_now)
        self.action_area.pack_end(self.connect_button)

        self.action_area.show_all()

    def sartup_connect_toggle(self, checkbutton, data=None):
        self.conf['connect_on_startup'] = checkbutton.get_active()

    def connect_now(self, widget, data=None):
        self.conf['host'] = self.host_entry.get_text()
        self.conf['port'] = int(self.port_entry.get_text())
        if self.conf['connect_on_startup']:
            self.conf.save()
        self.connect_cb(None, self.conf)
        self.hide()


# vim: ts=4 sw=4 expandtab
