// fileList.js

var panel_ref;
var Panel = function()
{
    panel_ref = this;
    this.ref = "panel_ref";
    this.dropSupport = false;

    this.module = "panel";
    this.tree = $("panel-tree");
    this.selected_playlist = null;
    this.selected_mode = null;
    // Activate this mode
    $("panel-source").hidden = false;

    this.treeController = false;

    this.__setPanel = function(panel)
    {
        var state = panel ? "visible" : "collapse";
        $('panel-select-button').checked = false;
        $('filter-box').style.visibility = state;
        $('panel-box').style.visibility = state;
        this.selected_playlist = null;
        this.selected_mode = panel ? "panel" : "panel-playlist";
    };

    this.update = function(obj)
    {
        var id = parseInt(obj.getAttribute("id"));
        if (id != this.treeId) {
            this.treeId = id;

            netscape.security.PrivilegeManager.
                enablePrivilege("UniversalXPConnect");
            var RDF = Components.classes["@mozilla.org/rdf/rdf-service;1"].
                getService(Components.interfaces.nsIRDFService);
            var ds = RDF.GetDataSource(window.location.href+"rdf/"+
                "panel"+"-"+this.treeId+".rdf");

            var pls_tree = $('panel-pls-list');
            pls_tree.view.selection.clearSelection();
            var mode = obj.getAttribute("type");
            if (mode == "playlist") {
                this.__setPanel(false);

                // select current playlist
                var items = pls_tree.getElementsByTagName("treerow");
                for (var i=0; item=items[i]; i++) {
                    if (item.getAttribute("value") ==
                            obj.getAttribute("value")){
                        pls_tree.view.selection.select(i);
                        break;
                        }
                    }
                this.selected_playlist = obj.getAttribute("value");
                }
            else if (mode == "panel") {
                this.__setPanel(true);

                // update filter bar
                $('panel-filter-text').value=
                    obj.getAttribute("filtertext_text");
                $('panel-filter-type').value=
                    obj.getAttribute("filtertext_type");
                // update panels
                var panels = Array("genre", "artist", "album");
                var selections = Array();
                for (t in panels) {
                    var pn = $(panels[t]+"-panel");

                    // remove old child
                    pn.clearSelection();

                    netscape.security.PrivilegeManager.
                        enablePrivilege("UniversalXPConnect");
                    // Update datasources

                    var currentSources = pn.database.GetDataSources();
                    while (currentSources.hasMoreElements()) {
                        var src = currentSources.getNext();
                        pn.database.RemoveDataSource(src);
                        }
                    pn.database.AddDataSource(ds);
                    pn.builder.rebuild();
                    this.showSelectedPanel(panels[t]);
                    }
                }

            var currentSources = this.tree.database.GetDataSources();
            while (currentSources.hasMoreElements()) {
                var src = currentSources.getNext();
                this.tree.database.RemoveDataSource(src);
                }
            this.tree.database.AddDataSource(ds);
            this.tree.builder.rebuild();

            $("panel-description").value = obj.getAttribute("description");
            // update playing
            if (this.playing != null)
                this.setPlaying(this.playing["pos"], this.playing["id"],
                    this.playing["state"]);
            }
    };

    this.updatePlaylistList = function(playlistList)
    {
        var tree = $("panel-pls-list");
        var tree_children = $("panel-pls-list-children");
        // first Erase the playlist list
        while(tree_children.hasChildNodes()){
            tree_children.removeChild(tree_children.firstChild);
            }

        // insert new playlist
        var Items = playlistList.getElementsByTagName("item");
        var selected_index = -1;
        for (var i=0;playlist=Items[i];i++) {
            var plsItem = document.createElement("treeitem");
            plsItem.setAttribute("value",playlist.getAttribute("id"));
            var plsRow = document.createElement("treerow");
            plsRow.setAttribute("value",playlist.getAttribute("id"));

            var cell = document.createElement("treecell");
            cell.setAttribute("label",playlist.firstChild.data);
            cell.setAttribute("properties","playlist-item");
            plsRow.appendChild(cell);

            var cell = document.createElement("treecell");
            cell.setAttribute("properties","remove-action");
            plsRow.appendChild(cell);

            plsItem.appendChild(plsRow);
            tree_children.appendChild(plsItem);

            if (playlist.getAttribute("id") == this.selected_playlist)
                selected_index = i;
            }
        // reselect current playlist
        if (selected_index != -1) {tree.view.selection.select(selected_index);}
    };

    this.updatePanelFilter = function(elt, tag)
    {
        var value = elt.getAttribute("value");
        ajaxdj_ref.send_post_command('panelUpdateFilter',{"type": "equals",
            "tag": tag, "value": value});
    };

    this.updatePanelFilterText = function()
    {
        var tag = $("panel-filter-type").value;
        var value = $("panel-filter-text").value;
        if (value == "")
            value = "__all__";
        ajaxdj_ref.send_post_command('panelUpdateFilter',
            {"type": "contains", "tag": tag, "value": value});
    };

    this.clearPanelFilterText = function()
    {
        $("panel-filter-text").value = "";
        this.updatePanelFilterText();
    };

    this.loadInQueue = function(pos)
    {
        var items = this.getTreeSelection("value");
        ajaxdj_ref.send_post_command("queueAdd", {"values": items, type: "id",
                                                  "pos": pos});
    };

    this.createPlaylist = function()
    {
        var pl_type = "static"; // TODO magic pls support
        var pl_name = $('newplaylist-entry').value;
        if (pl_name == "") { return; }
        ajaxdj_ref.send_post_command("playlistCreate", {"name": pl_name,
            type: pl_type});
        // hide panel
        $('newplaylist-panel').hidePopup();
    };

    this.showSelectedPanel = function(panel_type)
    {
        var pn = $(panel_type+"-panel");
        if (!pn.getRowCount()) { // panel not ready
            var cmd = this.ref+".showSelectedPanel('"+panel_type+"')";
            setTimeout(cmd,300);
            }
        else {
            // panel is now built
            // scroll to the selected item
            var idx = 0;
            while (idx < pn.getRowCount()) {
                var item = pn.getItemAtIndex(idx);
                if (item.getAttribute("selected") == "true") { break; }
                idx += 1;
                }
            idx = Math.min(idx+1, pn.getRowCount());
            pn.ensureIndexIsVisible(idx);
            }
    };

    // drop support for pls list
    this.plsDropSupport = new TreeDropSupport($('panel-pls-list'),
        function(pos, data) {
            if (pos == -1) { return; } // no playlist selected

            var pls = $('panel-pls-list').contentView.getItemAtIndex(pos);
            if (panel_ref.selected_playlist == pls.getAttribute("value"))
                return;

            if (data == 'panel') {
                var items = panel_ref.getTreeSelection("value");
                }
            else if (data == 'queue') {
                var items = queue_ref.getTreeSelection("value");
                }
            ajaxdj_ref.send_post_command('staticPlaylistAdd',
                {pl_id: pls.getAttribute("value"), values: items, type: 'id'});
            },
        Array('panel', 'queue'));
};
// heritage by prototype
Panel.prototype = new _Source;

var PlsPanelObserver = {
    setPlaylist: function (evt)
        {
            var tree = $('panel-pls-list');
            var childElement = {}, rowObject = {}, columnObject = {};
            tree.treeBoxObject.getCellAt(evt.clientX, evt.clientY, rowObject,
                columnObject, childElement);

            if (columnObject.value && rowObject.value != -1) {
                var item = tree.contentView.getItemAtIndex(rowObject.value);
                if (columnObject.value.index == 0)
                    this.selectPlaylist(item);
                else if (columnObject.value.index == 1)
                    this.removePlaylist(item);
                }
            return true;
        },
    selectPlaylist: function (item)
        {
            var pls = item.getAttribute("value");
            ajaxdj_ref.send_post_command('panelSet',
                {type: "playlist", value:pls});
        },
    removePlaylist: function(item)
        {
            var rs = window.confirm(ajaxdj_ref.getString("confirm"));
            if (rs) {
                var pls = item.getAttribute("value");
                var list = new Array(pls);
                ajaxdj_ref.send_post_command('playlistErase', {pl_ids: list});
                }
            else { this.selectPlaylist(item); }
        },
};

// vim: ts=4 sw=4 expandtab
