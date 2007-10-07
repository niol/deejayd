import os
import gtk
from djmote.utils.decorators import gui_callback
from deejayd.net.client import DeejaydWebradioList, DeejaydError

class WebradioBox(gtk.VBox, DeejaydWebradioList):

    def __init__(self, player):
        gtk.VBox.__init__(self)
        DeejaydWebradioList.__init__(self, player.get_server())
        self.__wb_id = None
        self.__player = player

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add_with_viewport(self.__build_tree())
        self.pack_start(scrolled_window)

        self.pack_start(self.__build_toolbar(), expand = False, fill = False)

    def update_status(self, status):
        if self.__wb_id == None or status["webradio"] > self.__wb_id:
            self.__wb_id = status["webradio"]
            self.get().add_callback(self.cb_build_list)
    
    def __build_tree(self):
        # ListStore
        # id, title, url
        wb_content = gtk.ListStore(int, str, str)

        # View
        # title, url
        self.__wb_view = gtk.TreeView(wb_content)

        title_col = gtk.TreeViewColumn("Title",gtk.CellRendererText(),text=1)
        self.__wb_view.append_column(title_col)

        url_col = gtk.TreeViewColumn("URL",gtk.CellRendererText(),text=2)
        self.__wb_view.append_column(url_col)

        # signals
        self.__wb_view.connect("row-activated",self.cb_play)

        return self.__wb_view

    def __build_toolbar(self):
        wb_toolbar = gtk.Toolbar()

        add_bt = gtk.ToolButton(gtk.STOCK_ADD)
        add_bt.connect("clicked",self.cb_add_dialog)
        wb_toolbar.insert(add_bt,0)

        clear_bt = gtk.ToolButton(gtk.STOCK_CLEAR)
        clear_bt.connect("clicked",self.cb_clear)
        wb_toolbar.insert(clear_bt,1)

        return wb_toolbar

    #
    # callbacks
    #
    @gui_callback
    def cb_build_list(self, answer):
        model = self.__wb_view.get_model()
        model.clear()
        try: media_list = answer.get_medias()
        except DeejaydError, err: self.__player.set_error(err)
        else:
            for w in media_list:
                model.append([w["id"], w["title"], w["url"]])

    def cb_play(self,treeview, path, view_column):
        model = self.__wb_view.get_model()
        iter = model.get_iter(path)
        id =  model.get_value(iter,0)
        self.__player.go_to(id)

    def cb_clear(self, widget):
        self.clear().add_callback(self.__player.cb_update_status)

    def cb_add_webradio(self,name,url):
        self.add_webradio(name,url).add_callback(self.__player.cb_update_status)

    def cb_add_dialog(self, widget):
        dialog = AddDialog(self)


class AddDialog(gtk.Dialog):

    def __init__(self, webradio):
        self.__webradio = webradio
        gtk.Dialog.__init__(self,"Add Webradio",None,\
            gtk.DIALOG_DESTROY_WITH_PARENT,
             (gtk.STOCK_ADD, gtk.RESPONSE_OK,\
              gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        layout = gtk.Table(rows=2, columns=2)

        name_label = gtk.Label('Name')
        layout.attach(name_label, 0, 1, 0, 1)
        self.name_entry = gtk.Entry(max=32)
        layout.attach(self.name_entry, 1, 2, 0, 1)

        url_label = gtk.Label('Url')
        layout.attach(url_label, 0, 1, 1, 2)
        self.url_entry = gtk.Entry(max=128)
        layout.attach(self.url_entry, 1, 2, 1, 2)

        self.vbox.pack_start(layout)
        self.connect("response", self.cb_response)
        self.show_all()

    def cb_response(self, dialog, response_id):
        if response_id == gtk.RESPONSE_CANCEL:
            self.destroy()
        elif response_id == gtk.RESPONSE_OK:
            name = self.name_entry.get_text()
            url = self.url_entry.get_text()
            if name != "" and url != "":
                self.__webradio.cb_add_webradio(name,url)
                self.destroy()

# vim: ts=4 sw=4 expandtab
