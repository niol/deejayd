import os
import gtk
from deejayd.net.client import DeejaydError
from djmote.utils.decorators import gui_callback
from djmote.widgets._base import SourceBox

class DvdBox(SourceBox):

    def __init__(self, player):
        SourceBox.__init__(self, player)
        self.__dvd_id = None

    def update_status(self, status):
        if self.__dvd_id == None or status["dvd"] > self.__dvd_id:
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

        title_col = gtk.TreeViewColumn("Title",gtk.CellRendererText(),text=1)
        self.dvd_view.append_column(title_col)

        url_col = gtk.TreeViewColumn("Length",gtk.CellRendererText(),text=2)
        self.dvd_view.append_column(url_col)

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
        model = self.__wb_view.get_model()
        iter = model.get_iter(path)
        id =  model.get_value(iter,0)
        self._player.go_to(id)

    @gui_callback
    def cb_build_content(self, answer):
        model = self.dvd_view.get_model()
        model.clear()

        try: content = answer.get_dvd_contents()
        except DeejaydError, err: self._player.set_error(err)
        else:
            for track in content["tracks"]:
                model.append([track['id'], "Title "+ track['id'],\
                              track['length']])


# vim: ts=4 sw=4 expandtab
