// fileList.js

var panel_ref;
var Panel = function()
{
    panel_ref = this;
    this.ref = "panel_ref";

    this.mediaDragged = true;
    this.module = "panel";
    this.tree = $("panel-tree");
    // Activate this mode
    $("panel-source").hidden = false;

    this.treeController = false;
    this.customUpdate = function(panel)
    {
        $("panel-description").value = panel.getAttribute("description");
        var mode = panel.getAttribute("type");
        if (mode == "playlist") {
            $('filter-box').style.visibility = "collapse";
            $('panel-box').style.visibility = "collapse";
            $('panel-list-entry').selected = false;
            }
        else {
            $('filter-box').style.visibility = "visible";
            $('panel-box').style.visibility = "visible";
            // select panel entry in left column
            $('panel-list-entry').selected = true;

            // update panels
            var panels = Array("genre", "artist", "album");
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
                    if (item.getAttribute("sel") == "true")
                        var selected_item = new_elt;
                    pn.appendChild(new_elt);
                    }
                pn.ensureElementIsVisible(selected_item);
                }
            }
        return true;
    };

    this.updatePlaylistList = function(playlistList)
    {
        var listbox = $("panel-pls-list");
        // first Erase the playlist list
        var Items = playlistList.getElementsByTagName("item");
        for (var i=0;playlist=Items[i];i++) {
            var plsItem = document.createElement("listitem");
            plsItem.setAttribute("label",playlist.firstChild.data);
            plsItem.setAttribute("type", "playlist");
            plsItem.setAttribute("context","panel-pls-menu");
            plsItem.setAttribute("value",playlist.getAttribute("name"));
            plsItem.className = "playlist-item listitem-iconic";
            plsItem.addEventListener("click",
                PanelObserver.selectPlaylist,true);

            listbox.appendChild(plsItem);
            }
    };

    this.removePlaylist = function()
    {
        var rs = window.confirm(ajaxdj_ref.getString("confirm"));
        if (rs) {
            // get selected playlist
            var plsList = new Array();
            for (var id in $("").selectedItems) {
                if (items[id].type == "playlist")
                    plsList.push(items[id].value);
                }
            ajaxdj_ref.send_post_command('playlistErase', {name: plsList});
            }
    };

    this.updatePanelFilter = function(elt, tag)
    {
        var value = elt.getAttribute("value");
        ajaxdj_ref.send_post_command('panelUpdateFilter',{"type": "panel-list",
            "tag": tag, "value": value});
    };

    this.updatePanelFilterText = function()
    {
        var tag = $("panel-filter-type").value;
        var value = $("filter-text").value;
        if (value == "")
            value = "__all__";
        ajaxdj_ref.send_post_command('panelUpdateFilter',
            {"type": "panel-text", "tag": tag, "value": value});
    };

    this.clearPanelFilterText = function()
    {
        $("filter-text").value = "";
        this.updatePanelFilterText();
    };
};
// heritage by prototype
Panel.prototype = new CommonTreeManagement;

var PanelObserver = {
    selectPlaylist: function (evt)
        {
            var pls = evt.target.getAttribute("value");
            ajaxdj_ref.send_post_command('panelSet',
                {type: "playlist", value:pls});
        },
};

// vim: ts=4 sw=4 expandtab
