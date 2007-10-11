import os
import gtk
from deejayd.net.client import DeejaydError
from djmote.utils.decorators import gui_callback

class VideoBox(gtk.VBox):

    def __init__(self, player):
        gtk.VBox.__init__(self)
        self.__player = player
        self.__video_dir = None

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add_with_viewport(self.__build_tree())
        self.pack_start(scrolled_window)

    def update_status(self, status):
        if self.__video_dir == None or status["video_dir"] != self.__video_dir:
            self.__video_dir = status["video_dir"]

            server = self.__player.get_server()
            server.get_video_dir(self.__video_dir).add_callback(self.cb_build)

    @gui_callback
    def cb_build(self, answer):
        model = self.video_view.get_model()
        model.clear()

        try: answer.get_contents()
        except DeejaydError, err: 
            self.__player.set_error(err)
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

    #
    # widget creation functions
    #
    def __build_tree(self):
        # ListStore
        # id, title, path, type, icon stock id
        video_content = gtk.ListStore(int, str, str, str, str)
        self.video_view = gtk.TreeView(video_content)

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

    def cb_row_activate(self, treeview, path, view_column):
        model = treeview.get_model()
        iter = model.get_iter(path)
        type =  model.get_value(iter,3)
        if type == "directory":
            self.__player.set_video_dir(model.get_value(iter,2))
        else:
            self.__player.go_to(model.get_value(iter,0))

# vim: ts=4 sw=4 expandtab
