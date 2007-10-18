
import gtk

class SourceBox(gtk.VBox):

    def __init__(self, player):
        gtk.VBox.__init__(self)
        self._player = player

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add_with_viewport(self._build_tree())
        self.pack_start(scrolled_window)

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
        tog_col = gtk.TreeViewColumn("Select",cell)
        tog_col.add_attribute(cell,'active',model_col)

        return tog_col

    def _create_treeview(self, model):
        tree_view = gtk.TreeView(model)
        tree_view.set_headers_visible(True)

        return tree_view

# vim: ts=4 sw=4 expandtab
