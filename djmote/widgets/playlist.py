import gtk
from deejayd.net.client import DeejaydPlaylist

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


class PlaylistBox(gtk.VBox, DeejaydPlaylist):

    def __init__(self, player):
        gtk.VBox.__init__(self)
        DeejaydPlaylist.__init__(self, player.get_server())
        self.__player = player
        self.__pl_id = None

        self.__build_tree()
        self.pack_start(self.__pl_view)

        self.__build_toolbar()
        self.pack_start(self.__pl_toolbar, expand = False, fill = False)

    def update_status(self, status):
        if self.__pl_id == None or status["playlist"] > self.__pl_id:
            self.__pl_id = status["playlist"]
            self.get().add_callback(self.cb_build_playlist)

    #
    # widget creation functions
    #
    def __build_tree(self):
        # ListStore
        # id, title, artist, album
        self.__pl_content = gtk.ListStore(int, str, str, str)

        # View
        # title, artist, album
        self.__pl_view = gtk.TreeView(self.__pl_content)
        self.__pl_view.set_vadjustment(gtk.Adjustment())

        # create column
        title_col = gtk.TreeViewColumn("Title")
        self.__pl_view.append_column(title_col)

        artist_col = gtk.TreeViewColumn("Artist")
        self.__pl_view.append_column(artist_col)

        album_col = gtk.TreeViewColumn("Album")
        self.__pl_view.append_column(album_col)

        # create cells
        title_cell = gtk.CellRendererText()
        title_col.pack_start(title_cell, True)
        title_col.set_attributes(title_cell, text=1)

        artist_cell = gtk.CellRendererText()
        artist_col.pack_start(artist_cell, True)
        artist_col.set_attributes(artist_cell, text=2)

        album_cell = gtk.CellRendererText()
        album_col.pack_start(album_cell, True)
        album_col.set_attributes(album_cell, text=3)

        # signals
        self.__pl_view.connect("row-activated",self.cb_play)

    def __build_toolbar(self):
        self.__pl_toolbar = gtk.Toolbar()

        clear_bt = gtk.ToolButton(gtk.STOCK_CLEAR)
        clear_bt.connect("clicked",self.cb_clear_playlist)
        self.__pl_toolbar.insert(clear_bt,0)

        shuffle_bt = gtk.ToolButton(gtk.STOCK_REFRESH)
        shuffle_bt.connect("clicked",self.cb_shuffle_playlist)
        self.__pl_toolbar.insert(shuffle_bt,1)

    #
    # callbacks
    #
    def cb_play(self,treeview, path, view_column):
        iter = self.__pl_content.get_iter(path)
        id =  self.__pl_content.get_value(iter,0)
        self.__player.go_to(id)

    def cb_clear_playlist(self, widget):
        self.clear().add_callback(self.__player.cb_update_status)

    def cb_shuffle_playlist(self, widget):
        self.shuffle().add_callback(self.__player.cb_update_status)

    @gui_callback
    def cb_build_playlist(self, answer):
        media_list = answer.get_medias()
        self.__pl_content.clear()

        for m in media_list:
            self.__pl_content.append([m["id"], m["title"],m["artist"],\
                                      m["album"]])


# vim: ts=4 sw=4 expandtab
