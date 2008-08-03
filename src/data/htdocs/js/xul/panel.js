// fileList.js

var panel_ref;
var Panel = function()
{
    panel_ref = this;
    this.ref = "panel_ref";

    this.module = "panel";
    this.tree = $("panel-tree");
    this.selected_playlist = null;
    // Activate this mode
    $("panel-source").hidden = false;

    this.treeController = false;
    this.customUpdate = function(panel)
    {
        var tree = $('panel-pls-list');
        tree.view.selection.clearSelection();
        $("panel-description").value = panel.getAttribute("description");
        var mode = panel.getAttribute("type");
        if (mode == "playlist") {
            $('panel-select-button').checked = false;
            $('filter-box').style.visibility = "collapse";
            $('panel-box').style.visibility = "collapse";

            // select current playlist
            var items = tree.getElementsByTagName("treerow");
            for (var i=0; item=items[i]; i++) {
                if (item.getAttribute("value") == panel.getAttribute("value")){
                    tree.view.selection.select(i);
                    break;
                    }
                }
            this.selected_playlist = panel.getAttribute("value");
            }
        else {
            $('panel-select-button').checked = true;
            $('filter-box').style.visibility = "visible";
            $('panel-box').style.visibility = "visible";
            this.selected_playlist = null;

            // update filter bar
            $('panel-filter-text').value=panel.getAttribute("filtertext_text");
            $('panel-filter-type').value=panel.getAttribute("filtertext_type");
            // update panels
            var panels = Array("genre", "artist", "album");
            var selections = Array();
            for (t in panels) {
                var pn = $(panels[t]+"-panel");

                // remove old child
                pn.clearSelection();
                var count = pn.getRowCount();
                while (count >= 0) {
                    pn.removeItemAt(count);
                    count -= 1;
                    }

                // build new child
                var pn_list = panel.getElementsByTagName(panels[t]+"-panel")[0];
                var items = pn_list.getElementsByTagName("item");
                for (var i=0; item=items[i]; i++) {
                    var new_elt = document.createElement('listitem');
                    new_elt.setAttribute("label", item.getAttribute("label"));
                    new_elt.setAttribute("value", item.getAttribute("value"));
                    new_elt.setAttribute("class", item.getAttribute("class"));
                    new_elt.setAttribute("selected", item.getAttribute("sel"));
                    new_elt.setAttribute("onclick",
                      "panel_ref.updatePanelFilter(this,'"+panels[t]+"');");
                    pn.appendChild(new_elt);
                    if (item.getAttribute("sel") == "true")
                        selections[t] = new_elt;
                    }
                }
            }
        return true;
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
};
// heritage by prototype
Panel.prototype = new CommonTreeManagement;

var PanelObserver = {
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
