import os
import gtk
from djmote.utils.decorators import gui_callback
from deejayd.net.client import DeejaydPlaylist

class PlaylistBox(gtk.VBox, DeejaydPlaylist):

    def __init__(self, player):
        gtk.VBox.__init__(self)
        DeejaydPlaylist.__init__(self, player.get_server())
        self.__player = player
        self.__pl_id = None

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add_with_viewport(self.__build_tree())
        self.pack_start(scrolled_window)

        self.pack_start(self.__build_toolbar(), expand = False, fill = False)

    def update_status(self, status):
        if self.__pl_id == None or status["playlist"] > self.__pl_id:
            self.__pl_id = status["playlist"]

            self.get().add_callback(self.cb_build_playlist)

    #
    # widget creation functions
    #
    def __build_tree(self):
        # ListStore
        # pos, id, title, artist, album
        self.__pl_content = gtk.ListStore(int, int, str, str, str)

        # View
        # pos, title, artist, album
        pl_view = gtk.TreeView(self.__pl_content)

        # create column
        pos_col = gtk.TreeViewColumn("Pos",gtk.CellRendererText(),text=0)
        pl_view.append_column(pos_col)

        title_col = gtk.TreeViewColumn("Title",gtk.CellRendererText(),text=2)
        pl_view.append_column(title_col)

        artist_col = gtk.TreeViewColumn("Artist",gtk.CellRendererText(),text=3)
        pl_view.append_column(artist_col)

        album_col = gtk.TreeViewColumn("Album",gtk.CellRendererText(),text=4)
        pl_view.append_column(album_col)

        # signals
        pl_view.connect("row-activated",self.cb_play)

        return pl_view

    def __build_toolbar(self):
        pl_toolbar = gtk.Toolbar()

        add_bt = gtk.ToolButton(gtk.STOCK_ADD)
        add_bt.connect("clicked",self.cb_open_file_dialog)
        pl_toolbar.insert(add_bt,0)

        clear_bt = gtk.ToolButton(gtk.STOCK_CLEAR)
        clear_bt.connect("clicked",self.cb_clear_playlist)
        pl_toolbar.insert(clear_bt,1)

        shuffle_bt = gtk.ToolButton(gtk.STOCK_REFRESH)
        shuffle_bt.connect("clicked",self.cb_shuffle_playlist)
        pl_toolbar.insert(shuffle_bt,2)

        save_bt = gtk.ToolButton(gtk.STOCK_SAVE)
        save_bt.connect("clicked",self.cb_open_save_dialog)
        pl_toolbar.insert(save_bt,3)

        return pl_toolbar

    #
    # callbacks
    #
    @gui_callback
    def cb_build_playlist(self, answer):
        media_list = answer.get_medias()
        self.__pl_content.clear()
        for m in media_list:
            self.__pl_content.append([m["pos"]+1, m["id"], m["title"],\
                        m["artist"], m["album"]])

    def cb_play(self,treeview, path, view_column):
        iter = self.__pl_content.get_iter(path)
        id =  self.__pl_content.get_value(iter,1)
        self.__player.go_to(id)

    def cb_clear_playlist(self, widget):
        self.clear().add_callback(self.__player.cb_update_status)

    def cb_shuffle_playlist(self, widget):
        self.shuffle().add_callback(self.__player.cb_update_status)

    def cb_open_file_dialog(self, widget):
        dialog = LibraryDialog(self, self.__player.get_server())

    def cb_open_save_dialog(self, widget):
        dialog = SaveDialog()

    def cb_add_song(self,path):
        self.add_song(path).add_callback(self.__player.cb_update_status)

    def cb_load(self,pl_name):
        self.load(pl_name).add_callback(self.__player.cb_update_status)


class LibraryDialog(gtk.Dialog):

    def __init__(self, playlist, server):
        self.__playlist = playlist
        self.__server = server
        gtk.Dialog.__init__(self,"Add songs to playlist",None,\
            gtk.DIALOG_DESTROY_WITH_PARENT,
             (gtk.STOCK_ADD, gtk.RESPONSE_OK,\
              gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos(gtk.POS_TOP)

        label = gtk.Label("Audio Library")
        self.notebook.append_page(self.__build_file_tree(),label)

        label = gtk.Label("Playlist List")
        self.notebook.append_page(self.__build_playlist_list(),label)

        self.vbox.pack_start(self.notebook)
        # signal
        self.connect("response", self.cb_response)
        self.set_size_request(450,350)
        self.show_all()

    def cb_response(self, dialog, response_id):
        if response_id == gtk.RESPONSE_CLOSE:
            self.destroy()
        elif response_id == gtk.RESPONSE_OK:
            if self.notebook.get_current_page() == 0:
                selection = self.library_view.get_selection()
                (model, iter) = selection.get_selected()
                if iter:
                    path =  model.get_value(iter,1)
                    self.__playlist.cb_add_song(path)
            else:
                selection = self.playlistlist_view.get_selection()
                (model, iter) = selection.get_selected()
                if iter:
                    pl_name =  model.get_value(iter,0)
                    self.__playlist.cb_load(pl_name)

    def __build_file_tree(self):
        # filename, path, type, icon stock id
        library_content = gtk.ListStore(str, str, str, str)
        self.library_view = gtk.TreeView(library_content)

        col = gtk.TreeViewColumn("Filename")
        # construct icon
        icon = gtk.CellRendererPixbuf()
        col.pack_start(icon)
        col.set_attributes(icon, stock_id = 3)
        # construct filename
        title = gtk.CellRendererText()
        col.pack_start(title)
        col.set_attributes(title, text = 0)

        self.library_view.append_column(col)

        # Signals
        self.library_view.connect("row-activated",self.update_file_list)
        self.update_file_list()

        # Set tree inside a ScrolledWindow
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        scrolled_window.add_with_viewport(self.library_view)
        return scrolled_window

    def update_file_list(self,treeview = None, path = None, view_column = None):

        if treeview == None: root_dir = ""
        else:
            model = treeview.get_model()
            iter = model.get_iter(path)
            type =  model.get_value(iter,2)
            if type != "directory":
                return
            root_dir = model.get_value(iter,1)

        @gui_callback
        def cb_build(answer):
            model = self.library_view.get_model()
            model.clear()
            for dir in answer.get_directories():
                model.append([dir, \
                    os.path.join(answer.root_dir,dir), "directory",\
                    gtk.STOCK_DIRECTORY])
            for file in answer.get_files():
                model.append([file["filename"], \
                    file["path"], file["type"], gtk.STOCK_FILE])

        self.__server.get_audio_dir(root_dir).add_callback(cb_build)

    def __build_playlist_list(self):
        # playlist_name, stock_id
        playlistlist_content = gtk.ListStore(str, str)
        self.playlistlist_view = gtk.TreeView(playlistlist_content)

        col = gtk.TreeViewColumn("Playlist Name")
        # construct icon
        icon = gtk.CellRendererPixbuf()
        col.pack_start(icon)
        col.set_attributes(icon, stock_id = 1)
        # construct playlist name
        name = gtk.CellRendererText()
        col.pack_start(name)
        col.set_attributes(name, text = 0)

        self.playlistlist_view.append_column(col)

        # Set tree inside a ScrolledWindow
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add_with_viewport(self.playlistlist_view)

        @gui_callback
        def cb_build(answer):
            model = self.playlistlist_view.get_model()
            for pl in answer.get_medias():
                model.append([pl["name"], gtk.STOCK_FILE])
        self.__server.get_playlist_list().add_callback(cb_build)

        return scrolled_window


class SaveDialog(gtk.Dialog):
    pass

# vim: ts=4 sw=4 expandtab
