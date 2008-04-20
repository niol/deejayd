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

import gobject, gtk, pango
from djmote.utils.decorators import gui_callback
from deejayd.net.client import DeejaydError
from djmote.const import CELL_FONT, CELL_BACKGROUND, PL_PAGER_LENGTH

def format_time(time):
    """Turn a time value in seconds into hh:mm:ss or mm:ss."""
    if time >= 3600: # 1 hour
        # time, in hours:minutes:seconds
        return "%d:%02d:%02d" % (time // 3600, (time % 3600) // 60, time % 60)
    else:
        # time, in minutes:seconds
        return "%d:%02d" % (time // 60, time % 60)

class ErrorDialog(gtk.Dialog):

    def __init__(self, widget, error):
        parent = widget and widget.get_parent_window()
        gtk.Dialog.__init__(self, "Error", parent,\
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,\
                            (gtk.STOCK_OK, gtk.RESPONSE_OK,)
                            )
        label = gtk.Label(error)
        self.vbox.pack_start(label)
        self.connect("response", lambda a,b: self.destroy())
        self.show_all()


class _BaseWidget:

    def execute(self, cmd, *__args, **__kw):
        cmd(*__args, **__kw).add_callback(self.cb_default)

    def subscribe(self):
        gobject.idle_add(self.__subscribe, priority=gobject.PRIORITY_HIGH)

    def __subscribe(self):
        for (sig_name, callback) in self._signals:
            try: sig_id = self.server.subscribe(sig_name,getattr(self,callback))
            except DeejaydError, err:
                self.error(err)
            else:
                self._signal_ids.append(sig_id)

    def unsubscribe(self):
        gobject.idle_add(self.__unsubscribe, priority=gobject.PRIORITY_HIGH)

    def __unsubscribe(self):
        for sig_id in self._signal_ids:
            try: self.server.unsubscribe(sig_id)
            except DeejaydError:
                pass

    @gui_callback
    def cb_default(self, answer):
        try: answer.get_contents()
        except DeejaydError, err:
            self.error(err)

    def error(self, err, widget = None):
        ErrorDialog(widget, str(err))


class _BaseBoxWithTree(_BaseWidget):

    def _build_select_column(self, model):
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

    def get_selection(self, id_col = 1, model = None):
        ids = []
        def create_selection(model, path, iter):
            toggled =  model.get_value(iter, 0)
            if toggled:
                ids.append(model.get_value(iter, id_col))

        m = model or self.tree_view.get_model()
        m.foreach(create_selection)

        return ids


class _BaseSourceBox(_BaseBoxWithTree):
    _toolbar_items = []
    source = None
    use_toggled = True

    def __init__(self, server):
        self.main_box = gtk.VBox()
        self.server = server

        # subscribe to signals
        self.subscribe()
        # build the widget
        self.build()

    def build(self):
        # toggled, id, markup, background_set
        model = gtk.ListStore('gboolean', int, str, 'gboolean')
        self.tree_view = DjmoteTreeView(model)

        # create columns
        if self.use_toggled:
            tog_col = self._build_select_column(model)
            self.tree_view.append_column(tog_col)

        cell= DjmoteCellRendererText()
        cell.set_property("background", CELL_BACKGROUND)
        col = gtk.TreeViewColumn("markup", cell, markup=2, background_set=3)
        self.tree_view.append_column(col)

        self.tree_view.connect("row-activated",self.goto)
        self.main_box.pack_start(DjmoteTreeBox(self.tree_view))

        # toolbar
        self._toolbox = gtk.HBox()
        toolbar, i = gtk.Toolbar(), 0
        for  (stock, action) in self._toolbar_items:
            bt = gtk.ToolButton(stock)
            bt.connect("clicked", getattr(self, action))
            toolbar.insert(bt, i)
            i += 1
        self._toolbox.pack_start(toolbar, expand = True, fill = True)

        # pager
        self.pager = {"current": 0, "total": 0}
        pbox = gtk.HBox()
        size = gtk.ICON_SIZE_MENU
        items = [
            ("first_btn", "button", gtk.STOCK_GOTO_FIRST, self.go_first),
            ("prev_btn", "button", gtk.STOCK_GO_BACK, self.go_previous),
            ("label", "label", "1/1", None),
            ("next_btn", "button", gtk.STOCK_GO_FORWARD, self.go_next),
            ("last_btn", "button", gtk.STOCK_GOTO_LAST, self.go_next),
            ]
        for (name, type, value, callback) in items:
            if type  == "button":
                w = DjmoteButton()
                w.set_image(gtk.image_new_from_stock(value, size))
                w.connect("clicked", callback)
            elif type == "label": w = gtk.Label(value)

            w.set_sensitive(False)
            pbox.pack_start(w, expand = False, fill = False)
            self.pager[name] = w

        self._toolbox.pack_start(pbox, expand = False, fill = True)
        self.main_box.pack_start(self._toolbox, expand = False, fill = True)
        self.update()

    def update(self, signal = None):
        self.get()

    def get(self, page = 1):
        self.set_loading()
        self.source.get((page-1)*PL_PAGER_LENGTH,\
            PL_PAGER_LENGTH).add_callback(self.cb_update)
        self.pager["current"] = page

    def set_loading(self):
        model = self.tree_view.get_model()
        model.clear()
        model.append([False, 0, "Loading", False])

    def goto(self, treeview, path, view_column):
        model = treeview.get_model()
        iter = model.get_iter(path)
        id =  model.get_value(iter,1)
        self.execute(self.server.go_to, id)

    def destroy(self):
        self.unsubscribe()
        self.main_box.destroy()

    @gui_callback
    def cb_update(self, answer):
        try: medias = answer.get_medias()
        except DeejaydError, err:
            self.error(err, self.main_box)
            return

        model = self.tree_view.get_model()
        model.clear()
        i = 0
        for media in medias:
            bg_set = i%2 == 0
            model.append([False, media["id"], self._format_text(media), bg_set])
            i += 1
        length = answer.get_total_length()
        if length > 0: # update pager
            self.pager["total"] = int(length)/PL_PAGER_LENGTH + 1
            self.pager["label"].set_text("%d/%d" %\
                (self.pager["current"], self.pager["total"]))
            for k, v in self.pager.items():
                try: v.set_sensitive(True)
                except AttributeError: pass

    def _format_text(self, media):
        raise NotImplementedError

    #
    # pager specific functions
    #
    def go_next(self, widget):
        if self.pager["current"] < self.pager["total"]:
            self.get(self.pager["current"] + 1)

    def go_previous(self, widget):
        if self.pager["current"] > 1:
            self.get(self.pager["current"] - 1)

    def go_first(self, widget):
        self.get(1)

    def go_last(self, widget):
        self.get(self.pager["total"])


class _BaseLibraryDialog(gtk.Dialog, _BaseBoxWithTree):
    type = ""
    _nblist_ = []
    _dialog_actions = ()

    def __init__(self, server, source):
        self.server = server
        self.source = source
        self.subscribe()

        gtk.Dialog.__init__(self,"%s library" % self.type,None,\
            gtk.DIALOG_DESTROY_WITH_PARENT, self._dialog_actions)

        # build notebook
        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos(gtk.POS_TOP)
        for label, func in self._nblist_:
            l = gtk.Label(label)
            self.notebook.append_page(getattr(self, func)(),l)
        self.vbox.pack_start(self.notebook)

        self.connect("response", self.cb_response)
        self.set_size_request(500,350)
        self.show_all()

    def destroy(self):
        self.unsubscribe()
        gtk.Dialog.destroy(self)

    def cb_response(self, dialog, response_id):
        raise NotImplementedError


class DjmoteTreeBox(gtk.HBox):

    def __init__(self, tree_view):
        gtk.HBox.__init__(self)
        scrollbar = gtk.VScrollbar()
        scrollbar.set_name("hildon-thumb-scrollbar")
        self.pack_start(scrollbar, expand = False, fill = False)
        scrollbar.set_adjustment(tree_view.get_vadjustment())
        self.pack_start(tree_view)


class DjmoteTreeView(gtk.TreeView):

    def __init__(self, model):
        gtk.TreeView.__init__(self, model)
        try: self.set_property("allow-checkbox-mode",False)
        except: pass # chinook

    def set_grid_lines(self):
        try: gtk.TreeView.set_grid_lines(self, \
                gtk.TREE_VIEW_GRID_LINES_HORIZONTAL)
        except AttributeError: pass # bora and gregale


class DjmoteCellRendererText(gtk.CellRendererText):

    def __init__(self):
        gtk.CellRendererText.__init__(self)
        self.set_property("ellipsize",pango.ELLIPSIZE_END)
        self.set_property("font-desc",pango.FontDescription(CELL_FONT))


class DjmoteButton(gtk.Button):

    def __init__(self):
        # The empty string label is there for the image to show on gtk 2.6.10
        gtk.Button.__init__(self, label='')

# vim: ts=4 sw=4 expandtab
