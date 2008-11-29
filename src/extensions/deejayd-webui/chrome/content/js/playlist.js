// playlist.js

var playlist_ref;

var Playlist = function()
{
    playlist_ref = this;
    this.ref = "playlist_ref";

    this.module = "playlist";
    this.tree = $("playlist-tree");
    // Activate this mode
    $("playlist-source").hidden = false;

    this.treeController = {
        supportsCommand : function(cmd){
            return (cmd == "cmd_delete"); },
        isCommandEnabled : function(cmd){return true;},
        doCommand : function(cmd){
            if (cmd == "cmd_delete")
                playlist_ref.removeItems();
            },
        onEvent : function(evt){ }
        };

    this.customUpdate = function(playlist)
    {
        // Update Playlist Description
        $("playlist-description").value =
            playlist.getAttribute("description");
        var saveDisabled = playlist.getAttribute("length") == "0" ?
            true : false;
        $("playlist-savebtn").disabled = saveDisabled;
    };

    this.togglePlaylistForm = function(print)
    {
        var plsForm = $('playlist-save-form');
        if (print == 1) {
            plsForm.style.display = "block";
            $('playlist-save-btn').selectedIndex = 1;
            $('playlist-save-list').focus();
            }
        else if (print == 0) {
            plsForm.style.display = "none";
            $('playlist-save-btn').selectedIndex = 0;
            $('playlist-save-list').value = "";
            }
    };

    this.savePlaylist = function()
    {
        var enable = true;
        var plsName = $('playlist-save-list').value;

        for (id in fileList_ref.playlistList) {
            if (plsName == fileList_ref.playlistList[id]) {
                enable = window.confirm(ajaxdj_ref.getString("replacePls"));
                break;
                }
            }

        if (enable) {
            ajaxdj_ref.send_post_command("playlistSave",{name:plsName});
            this.togglePlaylistForm(0);
            }
    };

    /********************************************************************/
    // custom drag and drop actions
    /********************************************************************/
    this.supportedDropData = Array('playlist', 'playlist-list',
                                   'directory-list', 'audio-file-list');
    this.dropAction = function(pos, data)
    {
        if (data == 'playlist') {
            // move song at the new position
            var s_ids = playlist_ref.getTreeSelection("id");
            ajaxdj_ref.send_post_command("playlistMove",
                {ids:s_ids, new_pos:pos});
            }
        else if ((data == 'directory-list') || (data == 'audio-file-list')) {
            fileList_ref.loadFiles(pos);
            }
        else if (data == 'playlist-list') { fileList_ref.loadPlaylist(pos); };
    }
};

// heritage by prototype
Playlist.prototype = new _Source;

// vim: ts=4 sw=4 expandtab
