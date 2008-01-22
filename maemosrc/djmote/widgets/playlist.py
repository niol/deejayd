# Djmote, a graphical deejayd client designed for use on Maemo devices
# Copyright (C) 2007 Mickael Royer <mickael.royer@gmail.com>
#                    Alexandre Rossi <alexandre.rossi@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os
import gobject,gtk,pango
from djmote.utils.decorators import gui_callback
from djmote.const import PL_PAGER_LENGTH
from deejayd.net.client import DeejaydPlaylist, DeejaydError
from djmote.widgets._base import *

class PlaylistBox(SourceBox, DeejaydPlaylist):

    def __init__(self, player):
        SourceBox.__init__(self, player)
        DeejaydPlaylist.__init__(self, player.get_server())
        self.__pl_id = None
        self.__pl_pager = None
        self.__pl_length = 0

    def update_status(self, status):
        if self.__pl_id == None or status["playlist"] != self.__pl_id:
            self.__pl_id = status["playlist"]
            self.__pl_length = status["playlistlength"]
            self._build_pager()

    #
    # widget creation functions
    #
    def _build_pager(self):
        if self.__pl_pager: # remove previous pager
            self.__pl_pager.destroy()
            self.__pl_pager = None

        nb = self.__pl_length/PL_PAGER_LENGTH
        if nb == 0: # pager not needed
            self.get().add_callback(self.cb_build_playlist)
            return

        self.__pl_pager = PagerBox(nb+1, self.cb_get_playlist_page)
        self.toolbar_box.pack_start(self.__pl_pager, expand = False)

    def _build_tree(self):
        # ListStore
        # id, title, artist, album, toggled
        self.__pl_content = gtk.ListStore(int, str, str, str, 'gboolean')
        self.__reset_playlist()

        # View
        # pos, title, artist, album
        pl_view = self._create_treeview(self.__pl_content)
        pl_view.set_fixed_height_mode(True)

        # create columns
        tog_col = self._build_select_column(self.cb_col_toggled, 4)
        pl_view.append_column(tog_col)

        self._build_text_columns(pl_view, [("Title",1,200),("Artist",2,100),\
            ("Album",3,100)])

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

    def cb_get_playlist_page(self, page = 1):
        self.get(PL_PAGER_LENGTH * (page-1), PL_PAGER_LENGTH).\
            add_callback(self.cb_build_playlist)

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

        self.__reset_playlist()
        self.del_songs(self.ids).add_callback(self._player.cb_update_status)
        del self.ids

    def cb_clear_playlist(self, widget):
        self.clear().add_callback(self._player.cb_update_status)

    def cb_shuffle_playlist(self, widget):
        self.__reset_playlist()
        self.shuffle().add_callback(self._player.cb_update_status)

    def cb_open_file_dialog(self, widget):
        dialog = LibraryDialog(self, self._player.get_server())

    def cb_open_save_dialog(self, widget):
        dialog = SaveDialog(self)

    def cb_add_songs(self,path):
        self.__reset_playlist()
        self.add_songs(path).add_callback(self._player.cb_update_status)

    def cb_loads(self,pl_names):
        self.__reset_playlist()
        self.loads(pl_names).add_callback(self._player.cb_update_status)

    def __reset_playlist(self):
        self.__pl_content.clear()
        self.__pl_content.append([0, "Refresh playlist, please wait...","","",\
                False])


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
        self.vbox.pack_start(self._build_toolbar(),expand = False,fill = False)
        # signal
        self.connect("response", self.cb_response)
        self.set_size_request(500,350)
        self.show_all()

    def _build_toolbar(self):
        self.toolbar_box = gtk.HBox()

        toolbar = gtk.Toolbar()
        toolbar.set_style(gtk.TOOLBAR_BOTH_HORIZ)
        refresh = gtk.ToolButton(gtk.STOCK_REFRESH)
        refresh.connect("clicked",self.cb_update_library)
        toolbar.insert(refresh,0)

        self.toolbar_box.pack_start(toolbar)
        return self.toolbar_box

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

            def untoggled(model, path, iter):
                model.set_value(iter,0,False)

            if self.notebook.get_current_page() == 0:
                model = self.library_view.get_model()
                model.foreach(create_selection, 2)
                if self.ids != []:
                    model.foreach(untoggled)
                    self.__playlist.cb_add_songs(self.ids)
            else:
                model = self.playlistlist_view.get_model()
                model.foreach(create_selection, 1)
                if self.ids != []:
                    model.foreach(untoggled)
                    self.__playlist.cb_loads(self.ids)
            del self.ids

    def __build_file_tree(self):
        # toggled, filename, path, type, icon stock id
        library_content = gtk.ListStore('gboolean', str, str, str, str)
        self.library_view = DjmoteTreeView(library_content)
        self.library_view.set_grid_lines()
        self.library_view.set_fixed_height_mode(True)

        tog_col = self.__build_select_column(library_content)
        self.library_view.append_column(tog_col)

        col = gtk.TreeViewColumn("Filename")
        col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        col.set_fixed_width(300)
        # construct icon
        icon = gtk.CellRendererPixbuf()
        icon.set_property("xpad",4)
        col.pack_start(icon,expand = False)
        col.set_attributes(icon, stock_id = 4)
        # construct filename
        title = gtk.CellRendererText()
        title.set_property("ellipsize",pango.ELLIPSIZE_END)
        title.set_property("font-desc",pango.FontDescription("Sans Normal 13"))
        col.pack_start(title)
        col.set_attributes(title, text = 1)

        self.library_view.append_column(col)

        # Signals
        self.library_view.connect("row-activated",self.update_file_list)
        self.update_file_list()

        # Set tree inside a ScrolledWindow
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add_with_viewport(self.library_view)
        return scrolled_window

    def update_file_list(self,treeview = None, path = None, view_column = None):
        model = self.library_view.get_model()
        if treeview == None: root_dir = ""
        else:
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

        model.clear()
        model.append([False, "Update audio dir/file list..","","message",\
                gtk.STOCK_REFRESH])
        self.__server.get_audio_dir(root_dir).add_callback(cb_build)

    def __build_playlist_list(self):
        # playlist_name, stock_id
        playlistlist_content = gtk.ListStore('gboolean', str, str)
        self.playlistlist_view = DjmoteTreeView(playlistlist_content)
        self.playlistlist_view.set_grid_lines()

        tog_col = self.__build_select_column(playlistlist_content)
        self.playlistlist_view.append_column(tog_col)

        col = gtk.TreeViewColumn("Playlist Name")
        # construct icon
        icon = gtk.CellRendererPixbuf()
        icon.set_property("xpad",4)
        col.pack_start(icon, expand = False)
        col.set_attributes(icon, stock_id = 2)
        # construct playlist name
        name = gtk.CellRendererText()
        name.set_property("font-desc",pango.FontDescription("Sans Normal 13"))
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
        tog_col = gtk.TreeViewColumn("",cell)
        tog_col.add_attribute(cell,'active',0)
        tog_col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        tog_col.set_fixed_width(40)

        return tog_col

    def cb_col_toggled(self, cell, path, model):
        model[path][0] = not model[path][0]

    @gui_callback
    def cb_update_trigger(self, ans):
        try: self.__update_id = ans["audio_updating_db"]
        except DeejaydError, err:
            return

        # create a progress bar
        self.progress_bar = gtk.ProgressBar()
        self.progress_bar.set_pulse_step(0.1)
        self.progress_bar.show()
        self.toolbar_box.pack_start(self.progress_bar, expand = False, \
            fill = False)

        # update status every second
        def update_verif():
            def cb_verif(ans):
                status = ans.get_contents()
                try : id = status["audio_updating_db"]
                except KeyError:
                    self.progress_bar.set_fraction(1.0)
                    del self.__update_id
                    self.progress_bar.destroy()
                    del self.progress_bar
                    self.update_file_list()
                else:
                    gobject.timeout_add(1000,update_verif)

            self.progress_bar.pulse()
            self.__server.get_status().add_callback(cb_verif)
        gobject.timeout_add(1000,update_verif)

    def cb_update_library(self,widget, data = None):
        self.__server.update_audio_library().add_callback(\
            self.cb_update_trigger)


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
