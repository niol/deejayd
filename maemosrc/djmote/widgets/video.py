import os
import gtk, gobject
from deejayd.net.client import DeejaydError
from djmote.utils.decorators import gui_callback
from djmote.widgets._base import SourceBox

class VideoBox(SourceBox):

    def __init__(self, player):
        SourceBox.__init__(self, player)
        self.__video_dir = None

    def update_status(self, status):
        if self.__video_dir == None or status["video_dir"] != self.__video_dir:
            self.__video_dir = status["video_dir"]

            server = self._player.get_server()
            server.get_video_dir(self.__video_dir).add_callback(self.cb_build)

    #
    # widget creation functions
    #
    def _build_tree(self):
        # ListStore
        # id, title, path, type, icon stock id
        video_content = gtk.ListStore(int, str, str, str, str)
        self.video_view = self._create_treeview(video_content)

        col = gtk.TreeViewColumn("Filename")
        # construct icon
        icon = gtk.CellRendererPixbuf()
        col.pack_start(icon)
        col.set_attributes(icon, stock_id = 4)
        # construct filename
        title = gtk.CellRendererText()
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

    #
    # callbacks
    #
    @gui_callback
    def cb_build(self, answer):
        model = self.video_view.get_model()
        model.clear()

        try: answer.get_contents()
        except DeejaydError, err:
            self._player.set_error(err)
            return

        if answer.root_dir != "":
            parent_dir = os.path.dirname(answer.root_dir)
            model.append([0,"..",parent_dir,"directory",gtk.STOCK_GOTO_TOP])

        for dir in answer.get_directories():
            path = os.path.join(self.__video_dir, dir)
            model.append([0, dir, path, "directory", gtk.STOCK_DIRECTORY])

        for file in answer.get_files():
            path = os.path.join(self.__video_dir, file["filename"])
            model.append([file["id"], \
                file["filename"], path, file["type"], gtk.STOCK_FILE])

    @gui_callback
    def cb_update_trigger(self, ans):
        try: self.__update_id = ans["video_updating_db"]
        except DeejaydError, err:
            self._player.set_error(err)
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
                try : id = status["video_updating_db"]
                except KeyError:
                    self.progress_bar.set_fraction(1.0)
                    del self.__update_id
                    self.progress_bar.destroy()
                    del self.progress_bar
                    self._player.set_video_dir("")
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
        type =  model.get_value(iter,3)
        if type == "directory":
            self._player.set_video_dir(model.get_value(iter,2))
        else:
            self._player.go_to(model.get_value(iter,0))

    def cb_update_library(self,widget, data = None):
        server = self._player.get_server()
        server.update_video_library().add_callback(self.cb_update_trigger)

# vim: ts=4 sw=4 expandtab
