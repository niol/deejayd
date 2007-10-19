import os
import gtk
from djmote.utils.decorators import gui_callback
from deejayd.net.client import DeejaydPlaylist, DeejaydError
from djmote.widgets._base import *

class PlaylistBox(SourceBox, DeejaydPlaylist):

    def __init__(self, player):
        SourceBox.__init__(self, player)
        DeejaydPlaylist.__init__(self, player.get_server())
        self.__pl_id = None

    def update_status(self, status):
        if self.__pl_id == None or status["playlist"] > self.__pl_id:
            self.__pl_id = status["playlist"]

            self.get().add_callback(self.cb_build_playlist)

    #
    # widget creation functions
    #
    def _build_tree(self):
        # ListStore
        # id, title, artist, album, toggled
        self.__pl_content = gtk.ListStore(int, str, str, str, 'gboolean')

        # View
        # pos, title, artist, album
        pl_view = self._create_treeview(self.__pl_content)

        # create column
        tog_col = self._build_select_column(self.cb_col_toggled, 4)
        pl_view.append_column(tog_col)

        title_col = gtk.TreeViewColumn("Title",gtk.CellRendererText(),text=1)
        pl_view.append_column(title_col)

        artist_col = gtk.TreeViewColumn("Artist",gtk.CellRendererText(),text=2)
        pl_view.append_column(artist_col)

        album_col = gtk.TreeViewColumn("Album",gtk.CellRendererText(),text=3)
        pl_view.append_column(album_col)

        # signals
        pl_view.connect("row-activated",self.cb_play)

        return pl_view

    def _build_toolbar(self):
        pl_toolbar = gtk.Toolbar()

        add_bt = gtk.ToolButton(gtk.STOCK_ADD)
        add_bt.connect("clicked",self.cb_open_file_dialog)
        pl_toolbar.insert(add_bt,0)

        del_bt = gtk.ToolButton(gtk.STOCK_REMOVE)
        del_bt.connect("clicked",self.cb_remove_song)
        pl_toolbar.insert(del_bt,1)

        clear_bt = gtk.ToolButton(gtk.STOCK_CLEAR)
        clear_bt.connect("clicked",self.cb_clear_playlist)
        pl_toolbar.insert(clear_bt,2)

        shuffle_bt = gtk.ToolButton(gtk.STOCK_REFRESH)
        shuffle_bt.connect("clicked",self.cb_shuffle_playlist)
        pl_toolbar.insert(shuffle_bt,3)

        save_bt = gtk.ToolButton(gtk.STOCK_SAVE)
        save_bt.connect("clicked",self.cb_open_save_dialog)
        pl_toolbar.insert(save_bt,4)

        return pl_toolbar

    #
    # callbacks
    #
    @gui_callback
    def cb_build_playlist(self, answer):
        try: media_list = answer.get_medias()
        except DeejaydError, err: self._player.set_error(err)
        else:
            self.__pl_content.clear()
            for m in media_list:
                self.__pl_content.append([m["id"], m["title"],\
                            m["artist"], m["album"], False])

    def cb_play(self,treeview, path, view_column):
        iter = self.__pl_content.get_iter(path)
        id =  self.__pl_content.get_value(iter,0)
        self._player.go_to(id)

    def cb_col_toggled(self, cell, path):
        self.__pl_content[path][4] = not self.__pl_content[path][4]

    def cb_remove_song(self, widget):
        self.ids = []
        def create_selection(model, path, iter):
            toggled =  model.get_value(iter,4)
            if toggled:
                self.ids.append(model.get_value(iter,0))
        self.__pl_content.foreach(create_selection)

        self.del_songs(self.ids).add_callback(self._player.cb_update_status)
        del self.ids

    def cb_clear_playlist(self, widget):
        self.clear().add_callback(self._player.cb_update_status)

    def cb_shuffle_playlist(self, widget):
        self.shuffle().add_callback(self._player.cb_update_status)

    def cb_open_file_dialog(self, widget):
        dialog = LibraryDialog(self, self._player.get_server())

    def cb_open_save_dialog(self, widget):
        dialog = SaveDialog(self)

    def cb_add_songs(self,path):
        self.add_songs(path).add_callback(self._player.cb_update_status)

    def cb_loads(self,pl_names):
        self.loads(pl_names).add_callback(self._player.cb_update_status)


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
            self.ids = []
            def create_selection(model, path, iter, col):
                toggled =  model.get_value(iter,0)
                if toggled:
                    val = model.get_value(iter,col)
                    if val != "": self.ids.append(val)

            if self.notebook.get_current_page() == 0:
                model = self.library_view.get_model()
                model.foreach(create_selection, 2)
                if self.ids != []: self.__playlist.cb_add_songs(self.ids)
            else:
                model = self.playlistlist_view.get_model()
                model.foreach(create_selection, 1)
                if self.ids != []: self.__playlist.cb_loads(self.ids)
            del self.ids

    def __build_file_tree(self):
        # toggled, filename, path, type, icon stock id
        library_content = gtk.ListStore('gboolean', str, str, str, str)
        self.library_view = DjmoteTreeView(library_content)

        tog_col = self.__build_select_column(library_content)
        self.library_view.append_column(tog_col)

        col = gtk.TreeViewColumn("Filename")
        # construct icon
        icon = gtk.CellRendererPixbuf()
        col.pack_start(icon)
        col.set_attributes(icon, stock_id = 4)
        # construct filename
        title = gtk.CellRendererText()
        col.pack_start(title)
        col.set_attributes(title, text = 1)

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
            type =  model.get_value(iter,3)
            if type != "directory":
                return
            root_dir = model.get_value(iter,2)

        @gui_callback
        def cb_build(answer):
            model = self.library_view.get_model()
            model.clear()

            if answer.root_dir != "":
                parent_dir = os.path.dirname(answer.root_dir)
                model.append([False, "..",parent_dir,"directory",\
                                gtk.STOCK_GOTO_TOP])
            for dir in answer.get_directories():
                model.append([False, dir, \
                    os.path.join(answer.root_dir,dir), "directory",\
                    gtk.STOCK_DIRECTORY])
            for file in answer.get_files():
                model.append([False, file["filename"], \
                    file["path"], file["type"], gtk.STOCK_FILE])

        self.__server.get_audio_dir(root_dir).add_callback(cb_build)

    def __build_playlist_list(self):
        # playlist_name, stock_id
        playlistlist_content = gtk.ListStore('gboolean', str, str)
        self.playlistlist_view = DjmoteTreeView(playlistlist_content)

        tog_col = self.__build_select_column(playlistlist_content)
        self.playlistlist_view.append_column(tog_col)

        col = gtk.TreeViewColumn("Playlist Name")
        # construct icon
        icon = gtk.CellRendererPixbuf()
        col.pack_start(icon)
        col.set_attributes(icon, stock_id = 2)
        # construct playlist name
        name = gtk.CellRendererText()
        col.pack_start(name)
        col.set_attributes(name, text = 1)

        self.playlistlist_view.append_column(col)

        # Set tree inside a ScrolledWindow
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add_with_viewport(self.playlistlist_view)

        @gui_callback
        def cb_build(answer):
            model = self.playlistlist_view.get_model()
            for pl in answer.get_medias():
                model.append([False, pl["name"], gtk.STOCK_FILE])
        self.__server.get_playlist_list().add_callback(cb_build)

        return scrolled_window

    def __build_select_column(self, model):
        cell = gtk.CellRendererToggle()
        cell.set_property('activatable', True)
        cell.connect( 'toggled', self.cb_col_toggled, model)
        tog_col = gtk.TreeViewColumn("Select",cell)
        tog_col.add_attribute(cell,'active',0)

        return tog_col

    def cb_col_toggled(self, cell, path, model):
        model[path][0] = not model[path][0]


class SaveDialog(gtk.Dialog):

    def __init__(self, playlist):
        self.__playlist = playlist
        gtk.Dialog.__init__(self,"Save playlist",None,\
            gtk.DIALOG_DESTROY_WITH_PARENT,
             (gtk.STOCK_SAVE, gtk.RESPONSE_OK,\
              gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        # build form
        label = gtk.Label("Enter the playlist name")
        self.vbox.pack_start(label)
        self.entry = gtk.Entry(64)
        self.vbox.pack_start(self.entry)


        # signal
        self.connect("response", self.cb_response)
        self.set_size_request(450,150)
        self.show_all()

    def cb_response(self, dialog, response_id):
        @gui_callback
        def cb_save_playlist(answer):
            try: answer.get_contents()
            except DeejaydError, err:
                label = gtk.Label("Error : " + err)
                self.vbox.pack_end(label)
            else:
                self.destroy()

        if response_id == gtk.RESPONSE_CANCEL:
            self.destroy()
        elif response_id == gtk.RESPONSE_OK:
            pl_name = self.entry.get_text()
            if pl_name != "":
                self.__playlist.save(pl_name).add_callback(cb_save_playlist)

# vim: ts=4 sw=4 expandtab
