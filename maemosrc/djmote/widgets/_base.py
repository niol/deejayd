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

import gtk,pango

def fraction_seconds(seconds, hour = False):
    def format_number(n):
        if n < 10:
            return "0%d" % n
        return "%d" % n

    try: seconds = int(seconds)
    except ValueError: return "00"

    min, s = divmod(seconds, 60)
    if hour:
        h, min = divmod(min, 60)
        return "%s:%s:%s" % (format_number(h), format_number(min),\
                             format_number(s))
    return "%d:%d" % (format_number(min), format_number(s))


class DjmoteTreeView(gtk.TreeView):

    def __init__(self, model):
        gtk.TreeView.__init__(self, model)
        try: self.set_property("allow-checkbox-mode",False)
        except: pass # chinook

    def set_grid_lines(self):
        try: gtk.TreeView.set_grid_lines(self, \
                gtk.TREE_VIEW_GRID_LINES_HORIZONTAL)
        except AttributeError: pass # bora and gregale


class DjmoteButton(gtk.Button):

    def __init__(self):
        # The empty string label is there for the image to show on gtk 2.6.10
        gtk.Button.__init__(self, label='')
        # Needed for chinook
        settings = self.get_settings()
        settings.set_property("gtk-button-images", True)


class SourceBox(gtk.VBox):

    def __init__(self, player):
        gtk.VBox.__init__(self)
        self._player = player

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add_with_viewport(self._build_tree())
        self.pack_start(scrolled_window)

        # FOR FUTURE USE : thumb scrollbar
        #vscrollbar = scrolled_window.get_vscrollbar()
        #vscrollbar.set_name("hildon-thumb-scrollbar")
        # set the scrollbar at left
        #scrolled_window.set_placement(gtk.CORNER_TOP_RIGHT)

        # toolbar
        self.toolbar_box = gtk.HBox()
        self.toolbar_box.pack_start(self._build_toolbar(), \
            expand = True, fill = True)
        self.pack_start(self.toolbar_box, expand = False, fill = True)

    def update_status(self, status):
        pass

    def _build_tree(self):
        raise NotImplementedError

    def _build_toolbar(self):
        raise NotImplementedError

    def _build_select_column(self, cb_func, model_col):
        cell = gtk.CellRendererToggle()
        cell.set_property('activatable', True)
        cell.connect( 'toggled', cb_func)
        tog_col = gtk.TreeViewColumn("",cell)
        tog_col.add_attribute(cell,'active',model_col)
        tog_col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        tog_col.set_fixed_width(40)

        return tog_col

    def _build_text_columns(self, treeview, columns):
        for (title,id,size) in columns:
            cell= gtk.CellRendererText()
            cell.set_property("ellipsize",pango.ELLIPSIZE_END)
            cell.set_property("font-desc",\
                pango.FontDescription("Sans Normal 13"))
            col = gtk.TreeViewColumn(title,cell,text=id)
            col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            col.set_fixed_width(size)
            col.set_expand(True)
            treeview.append_column(col)

    def _create_treeview(self, model):
        tree_view = DjmoteTreeView(model)
        tree_view.set_headers_visible(True)
        tree_view.set_grid_lines()

        return tree_view


class PagerBox(gtk.HBox):

    def __init__(self, page_nb, callback):
        gtk.HBox.__init__(self)
        self.__current_page = 1
        self.__page_nb = page_nb
        self.__callback = callback

        first_button = DjmoteButton()
        first_button.set_image(gtk.image_new_from_stock(gtk.STOCK_GOTO_FIRST,\
            gtk.ICON_SIZE_MENU))
        first_button.connect("clicked",self.go_first)
        self.pack_start(first_button,expand = False, fill = False)

        prev_button = DjmoteButton()
        prev_button.set_image(gtk.image_new_from_stock(gtk.STOCK_GO_BACK,\
            gtk.ICON_SIZE_MENU))
        prev_button.connect("clicked",self.go_previous)
        self.pack_start(prev_button,expand = False, fill = False)

        self.__label = gtk.Label("1/%d" % page_nb)
        self.pack_start(self.__label,expand=False,fill=False)

        next_button = DjmoteButton()
        next_button.set_image(gtk.image_new_from_stock(gtk.STOCK_GO_FORWARD,\
            gtk.ICON_SIZE_MENU))
        next_button.connect("clicked",self.go_next)
        self.pack_start(next_button,expand = False, fill = False)

        last_button = DjmoteButton()
        last_button.set_image(gtk.image_new_from_stock(gtk.STOCK_GOTO_LAST,\
            gtk.ICON_SIZE_MENU))
        last_button.connect("clicked",self.go_last)
        self.pack_start(last_button,expand = False, fill = False)

        self.show_all()
        callback(self.__current_page)

    def go_next(self, widget):
        if self.__current_page < self.__page_nb:
            self.__update(self.__current_page + 1)

    def go_previous(self, widget):
        if self.__current_page > 1:
            self.__update(self.__current_page - 1)

    def go_first(self, widget):
        self.__update(1)

    def go_last(self, widget):
        self.__update(self.__page_nb)

    def __update(self, page):
        self.__current_page = page
        self.__label.set_text("%d/%d" %(self.__current_page,self.__page_nb))
        self.__callback(self.__current_page)

# vim: ts=4 sw=4 expandtab
