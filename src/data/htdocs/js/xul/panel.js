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

    this.setPlaylist = function(pls)
    {
    }

    this.updatePanel = function()
    {

    };

};
// heritage by prototype
Panel.prototype = new CommonTreeManagement;

// vim: ts=4 sw=4 expandtab
