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
import gtk, gobject, pango
from deejayd.net.client import DeejaydError
from djmote.utils.decorators import gui_callback
from djmote.widgets._base import _BaseSourceBox, _BaseLibraryDialog,\
                                DjmoteTreeView, format_time, DjmoteTreeBox

class VideoBox(_BaseSourceBox):
    use_toggled = False
    _toolbar_items = [
        (gtk.STOCK_ADD, "select_directory"),
        ]

    def __init__(self, server):
        self._signals = [ ("video.update", "update") ]
        self._signal_ids = []
        self.source = server.get_video()
        _BaseSourceBox.__init__(self, server)

    def _format_text(self, m):
        return " %s - %s\n\tlength : <i>%s</i>"\
            % (str(m["pos"]+1), m["title"], format_time(m["length"]))

    def select_directory(self, widget):
        LibraryDialog(self.source, self.server)


class LibraryDialog(_BaseLibraryDialog):
    type = "Video"
    _nblist_ = [("Select a directory", "build_library"),\
                ("Search", "search_box")]
    _dialog_actions = (gtk.STOCK_APPLY, gtk.RESPONSE_OK,\
                       gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)

    def __init__(self, source, server):
        self._signals = [ ("mediadb.vupdate", "update_library") ]
        self._signal_ids = []
        _BaseLibraryDialog.__init__(self, server, source)

    def cb_response(self, dialog, response_id):
        @gui_callback
        def cb_video_set(answer):
            try: answer.get_contents()
            except DeejaydError, err:
                label = gtk.Label("Error : " + err)
                self.vbox.pack_end(label)
            else:
                self.destroy()

        if response_id == gtk.RESPONSE_CLOSE:
            self.destroy()
        elif response_id == gtk.RESPONSE_OK:
            if self.notebook.get_current_page() == 0: # select directory
                selection = self.library_view.get_selection()
                model, iter = selection.get_selected()
                if not iter: return
                value, type = model.get_value(iter, 1), "directory"
            else:  # search box
                if self.search_entry.get_text() == "": return
                value, type = self.search_entry.get_text(), "search"
            self.source.set(value, type).add_callback(cb_video_set)

    def build_library(self):
        # filename, path, type, icon stock id
        library_content = gtk.ListStore(str, str, str, str)
        self.library_view = DjmoteTreeView(library_content)
        self.library_view.set_grid_lines()
        self.library_view.set_fixed_height_mode(True)

        col = gtk.TreeViewColumn("Filename")
        col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        col.set_fixed_width(300)
        # construct icon
        icon = gtk.CellRendererPixbuf()
        icon.set_property("xpad",4)
        col.pack_start(icon,expand = False)
        col.set_attributes(icon, stock_id = 3)
        # construct filename
        title = gtk.CellRendererText()
        title.set_property("ellipsize",pango.ELLIPSIZE_END)
        title.set_property("font-desc",pango.FontDescription("Sans Normal 13"))
        col.pack_start(title)
        col.set_attributes(title, text = 0)

        self.library_view.append_column(col)
        self.library_view.connect("row-activated",self.update_library)
        self.update_library()

        # Set tree inside a ScrolledWindow
        return DjmoteTreeBox(self.library_view)

    def update_library(self,treeview = None, path = None, view_column = None):
        model = self.library_view.get_model()
        if treeview == None: root_dir = ""
        else:
            iter = model.get_iter(path)
            type =  model.get_value(iter,2)
            if type != "directory":
                return
            root_dir = model.get_value(iter,1)

        @gui_callback
        def cb_build(answer):
            model = self.library_view.get_model()
            model.clear()

            if answer.root_dir != "":
                parent_dir = os.path.dirname(answer.root_dir)
                model.append(["..",parent_dir,"directory", gtk.STOCK_GOTO_TOP])
            for dir in answer.get_directories():
                model.append([dir, \
                    os.path.join(answer.root_dir,dir), "directory",\
                    gtk.STOCK_DIRECTORY])

        model.clear()
        model.append(["Update video dir/file list..","","message",\
                gtk.STOCK_REFRESH])
        self.server.get_video_dir(root_dir).add_callback(cb_build)

    def search_box(self):
        vbox = gtk.VBox()
        label = gtk.Label("Enter search words")
        vbox.pack_start(label, expand = False, fill = False)
        self.search_entry = gtk.Entry(64)
        vbox.pack_start(self.search_entry)

        return vbox

# vim: ts=4 sw=4 expandtab
