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
import gtk
from deejayd.net.client import DeejaydError
from djmote.utils.decorators import gui_callback
from djmote.widgets._base import SourceBox,fraction_seconds

class DvdBox(SourceBox):

    def __init__(self, player):
        SourceBox.__init__(self, player)
        self.__dvd_id = None
        self.__dvd_title = None

    def update_status(self, status):
        if self.__dvd_id == None or status["dvd"] != self.__dvd_id:
            self.__dvd_id = status["dvd"]
            server = self._player.get_server()
            server.get_dvd_content().add_callback(self.cb_build_content)

    #
    # widget creation functions
    #
    def _build_tree(self):
        # ListStore
        # id, title, length
        dvd_content = gtk.ListStore(str, str, str)
        self.dvd_view = self._create_treeview(dvd_content)
        self.dvd_view.set_fixed_height_mode(True)

        # create columns
        self._build_text_columns(self.dvd_view, \
            [("Title",1,300),("Length",2,100)])

        # signals
        self.dvd_view.connect("row-activated", self.cb_play)
        return self.dvd_view

    def _build_toolbar(self):
        dvd_toolbar = gtk.Toolbar()

        refresh_bt = gtk.ToolButton(gtk.STOCK_REFRESH)
        refresh_bt.connect("clicked",self._player.dvd_reload)
        dvd_toolbar.insert(refresh_bt,0)

        return dvd_toolbar

    #
    # callbacks
    #
    def cb_play(self,treeview, path, view_column):
        model = self.dvd_view.get_model()
        iter = model.get_iter(path)
        id =  model.get_value(iter,0)
        self._player.go_to(id)

    @gui_callback
    def cb_build_content(self, answer):
        if self.__dvd_title:
            self.__dvd_title.destroy()
        model = self.dvd_view.get_model()
        model.clear()

        try: content = answer.get_dvd_contents()
        except DeejaydError, err: self._player.set_error(err)
        else:
            # update title
            self.__dvd_title = gtk.Label(content['title'])
            self.toolbar_box.pack_start(self.__dvd_title, expand = False,\
                fill = False)
            self.__dvd_title.show()

            # update track
            for track in content["track"]:
                model.append([track['ix'], "Title "+ track['ix'],\
                              fraction_seconds(track['length'],True)])


# vim: ts=4 sw=4 expandtab
