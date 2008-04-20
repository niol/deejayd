# Djmote, a graphical deejayd client designed for use on Maemo devices
# Copyright (C) 2007-2008 Mickael Royer <mickael.royer@gmail.com>
#                         Alexandre Rossi <alexandre.rossi@gmail.com>
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
from djmote.widgets._base import _BaseSourceBox, _BaseLibraryDialog,\
                                 DjmoteTreeView, _BaseWidget,\
                                 DjmoteTreeBox, format_time


class PlaylistBox(_BaseSourceBox):
    _toolbar_items = [
        (gtk.STOCK_ADD, "open_file_dialog"),
        (gtk.STOCK_REMOVE, "remove_songs"),
        (gtk.STOCK_CLEAR, "clear_playlist"),
        (gtk.STOCK_REFRESH, "shuffle_playlist"),
        (gtk.STOCK_SAVE, "open_save_dialog"),
        ]

    def __init__(self, player):
        self._signals = [ ("player.plupdate", "update") ]
        self._signal_ids = []
        self.source = player.get_playlist()
        _BaseSourceBox.__init__(self, player)

    def _format_text(self, m):
        return "%d - %s (%s)\n\t<b>%s</b> - <i>%s</i>" %\
            (m["pos"]+1, gobject.markup_escape_text(m["title"]),\
             format_time(m["length"]),\
             gobject.markup_escape_text(m["artist"]),\
             gobject.markup_escape_text(m["album"]))

    def remove_songs(self, widget):
        ids = self.get_selection()
        if ids != []:
            self.set_loading()
            self.execute(self.source.del_songs, ids)

    def clear_playlist(self, widget):
        self.set_loading()
        self.execute(self.source.clear)

    def shuffle_playlist(self, widget):
        self.set_loading()
        self.execute(self.source.shuffle)

    def open_file_dialog(self, widget):
        LibraryDialog(self.server, self.source)

    def open_save_dialog(self, widget):
        SaveDialog(self.source)


class LibraryDialog(_BaseLibraryDialog):
    type = "Audio"
    _nblist_ = [("Library", "build_library"),\
                ("Playlist", "build_playlistlist")]
    _dialog_actions = (gtk.STOCK_ADD, gtk.RESPONSE_OK,\
                       gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)

    def __init__(self, server, source):
        self._signals = [ ("mediadb.aupdate", "update_file_list") ]
        self._signal_ids = []
        _BaseLibraryDialog.__init__(self, server, source)

    def add_songs(self,path):
        self.execute(self.source.add_songs, path)

    def loads_playlist(self,pl_names):
        self.execute(self.source.loads, pl_names)

    def cb_response(self, dialog, response_id):
        if response_id == gtk.RESPONSE_CLOSE:
            self.destroy()
        elif response_id == gtk.RESPONSE_OK:
            def untoggled(model, path, iter):
                model.set_value(iter,0,False)

            if self.notebook.get_current_page() == 0:
                model = self.library_view.get_model()
                ids = self.get_selection(2, model)
                if ids != []: self.add_songs(ids)
            else:
                model = self.playlistlist_view.get_model()
                names = self.get_selection(1, model)
                if names != []: self.loads_playlist(names)
            model.foreach(untoggled)

    def build_library(self):
        # toggled, filename, path, type, icon stock id
        library_content = gtk.ListStore('gboolean', str, str, str, str)
        self.library_view = DjmoteTreeView(library_content)
        self.library_view.set_grid_lines()
        self.library_view.set_fixed_height_mode(True)

        tog_col = self._build_select_column(library_content)
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
        return DjmoteTreeBox(self.library_view)

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
        self.server.get_audio_dir(root_dir).add_callback(cb_build)

    def build_playlistlist(self):
        # playlist_name, stock_id
        playlistlist_content = gtk.ListStore('gboolean', str, str)
        self.playlistlist_view = DjmoteTreeView(playlistlist_content)
        self.playlistlist_view.set_grid_lines()

        tog_col = self._build_select_column(playlistlist_content)
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

        @gui_callback
        def cb_build(answer):
            model = self.playlistlist_view.get_model()
            for pl in answer.get_medias():
                model.append([False, pl["name"], gtk.STOCK_FILE])
        self.server.get_playlist_list().add_callback(cb_build)

        return DjmoteTreeBox(self.playlistlist_view)


class SaveDialog(gtk.Dialog, _BaseWidget):

    def __init__(self, source):
        self.source = source
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
                self.source.save(pl_name).add_callback(cb_save_playlist)

# vim: ts=4 sw=4 expandtab
