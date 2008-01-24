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
from djmote.widgets._base import SourceBox

class VideoBox(SourceBox):

    def __init__(self, player):
        SourceBox.__init__(self, player)
        self.__video_id = None
        self.__video_label = None

    def update_status(self, status):
        if self.__video_id == None or status["video"] != self.__video_id:
            self.__video_id = status["video"]
            server = self._player.get_server()
            self.__reset_tree()
            server.get_videolist().add_callback(self.cb_build_list)
            self._build_label(status)

    #
    # widget creation functions
    #
    def _build_tree(self):
        # ListStore
        # id, title
        video_content = gtk.ListStore(int, str)
        self.video_view = self._create_treeview(video_content)
        self.video_view.set_fixed_height_mode(True)

        col = gtk.TreeViewColumn("Title")
        col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        # construct title
        title = gtk.CellRendererText()
        title.set_property("font-desc",pango.FontDescription("Sans Normal 13"))
        col.pack_start(title)
        col.set_attributes(title, text = 1)

        self.video_view.append_column(col)

        # Signals
        self.video_view.connect("row-activated",self.cb_row_activate)

        return self.video_view

    def _build_toolbar(self):
        toolbar = gtk.Toolbar()
        toolbar.set_style(gtk.TOOLBAR_BOTH_HORIZ)

        refresh = gtk.ToolButton(gtk.STOCK_REFRESH)
        refresh.connect("clicked",self.cb_update_library)
        toolbar.insert(refresh,0)

        return toolbar

    def _build_label(self, status):
        self._destroy_label()
        self.__video_label = gtk.Label("%s Videos" % status["videolength"])
        self.__video_label.show()
        self.toolbar_box.pack_start(self.__video_label, expand = False, \
            fill = False)

    def _destroy_label(self):
        if self.__video_label:
            self.__video_label.destroy()
            self.__video_label = None

    #
    # callbacks
    #
    @gui_callback
    def cb_build_list(self, answer):
        model = self.video_view.get_model()
        model.clear()

        try: answer.get_contents()
        except DeejaydError, err:
            self._player.set_error(err)
            return

        for media in answer.get_medias():
            model.append([media["id"], media["title"]])

    @gui_callback
    def cb_update_trigger(self, ans):
        try: self.__update_id = ans["video_updating_db"]
        except DeejaydError, err:
            self._player.set_error(err)
            return

        # create a progress bar but first destroy label
        self._destroy_label()
        self.progress_bar = gtk.ProgressBar()
        self.progress_bar.set_pulse_step(0.1)
        self.progress_bar.show()
        self.toolbar_box.pack_start(self.progress_bar, expand = False, \
            fill = False)

        # update status every second
        def update_verif():
            def cb_verif(ans):
                status = ans.get_contents()
                try : id = status["video_updating_db"]
                except KeyError:
                    self.progress_bar.set_fraction(1.0)
                    del self.__update_id
                    self.progress_bar.destroy()
                    del self.progress_bar
                    self._player.set_banner("Video library has been updated")
                else:
                    gobject.timeout_add(1000,update_verif)

            self.progress_bar.pulse()
            server = self._player.get_server()
            server.get_status().add_callback(cb_verif)

        gobject.timeout_add(1000,update_verif)

    def cb_row_activate(self, treeview, path, view_column):
        model = treeview.get_model()
        iter = model.get_iter(path)
        self._player.go_to(model.get_value(iter,0))

    def cb_update_library(self,widget, data = None):
        server = self._player.get_server()
        server.update_video_library().add_callback(self.cb_update_trigger)

    def __reset_tree(self):
        model = self.video_view.get_model()
        model.clear()
        model.append([0, "Update video list.."])

# vim: ts=4 sw=4 expandtab
