import gtk
from deejayd.net.client import DeejaydPlaylist

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

            def cb_build_playlist(answer):
                media_list = answer.get_medias()
                self.__pl_content.clear()
                for m in media_list:
                    self.__pl_content.append([m["pos"]+1, m["id"], m["title"],\
                                m["artist"], m["album"]])

            self.get().add_callback(cb_build_playlist)

    #
    # widget creation functions
    #
    def __build_tree(self):
        # ListStore
        # pos, id, title, artist, album
        self.__pl_content = gtk.ListStore(int, int, str, str, str)

        # View
        # pos, title, artist, album
        self.__pl_view = gtk.TreeView(self.__pl_content)

        # create column
        pos_col = gtk.TreeViewColumn("Pos",gtk.CellRendererText(),text=0)
        self.__pl_view.append_column(pos_col)

        title_col = gtk.TreeViewColumn("Title",gtk.CellRendererText(),text=2)
        self.__pl_view.append_column(title_col)

        artist_col = gtk.TreeViewColumn("Artist",gtk.CellRendererText(),text=3)
        self.__pl_view.append_column(artist_col)

        album_col = gtk.TreeViewColumn("Album",gtk.CellRendererText(),text=4)
        self.__pl_view.append_column(album_col)

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


# vim: ts=4 sw=4 expandtab
