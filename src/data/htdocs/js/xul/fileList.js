// fileList.js

var fileList_ref;

var FileList = function()
{
    fileList_ref = this;
    this.menuId = "navigation-path";
    this.menuCommand = "getdir";
    this.contextMenuId = "fileList-menu";
    this.dragItemType = null;
    this.playlistList = new Array();
    this.updateBox = "audio-update";
    this.listType = "audio";

    this.init = function()
    {
        try{
            netscape.security.PrivilegeManager.
                enablePrivilege("UniversalXPConnect");
            }
        catch(ex){return}
        var fileList = $('file-content');
        var fileListController = {
            supportsCommand : function(cmd){ return (cmd == "cmd_selectAll"); },
            isCommandEnabled : function(cmd){return true; },
            doCommand : function(cmd) { slAll('file-content'); },
            onEvent : function(evt){ }
            };

        var playlistList = $('playlistList-content');
        var playlistListController = {
            supportsCommand : function(cmd){
                return (cmd == "cmd_selectAll" || cmd == "cmd_delete"); },
            isCommandEnabled : function(cmd){return true;},
            doCommand : function(cmd){
                if (cmd == "cmd_selectAll")
                    slAll('playlistList-content');
                else if (cmd == "cmd_delete")
                    fileList_ref.erasePlaylist();
                },
            onEvent : function(evt){ }
            };

        playlistList.controllers.appendController(playlistListController);
        fileList.controllers.appendController(fileListController);
    };

    this.getDir = function(e)
    {
        var args = {};
        if (this.id !='root_link')
            args['dir'] = this.id;
        ajaxdj_ref.send_post_command("getdir",args);
    };

    this.updateFileList = function(fileList,dir)
    {
        this.curDir = dir;
        this.constructMenu(dir);
        this.constructItemList(fileList,"file-content");
    };

    this.loadCommand = function()
    {
        if ($('file-content').selectedCount > 0)
            this.loadFiles(-1);
        else if ($('playlistList-content').selectedCount > 0)
            this.loadPlaylist(-1);
    }

    this.loadItems = function(pos)
    {
        if (this.dragItemType == "playlist")
            this.loadPlaylist(pos);
        else
            this.loadFiles(pos);
    };

    this.loadItemsInQueue = function(pos)
    {
        if (this.dragItemType == "playlist")
            this.loadPlaylistInQueue(pos);
        else
            this.loadFilesInQueue(pos);
    };

    this.loadFiles = function(pos)
    {
        this.dragItemType = null;
        ajaxdj_ref.send_post_command('playlistAdd&pos='+pos,
            {path: this.getSelectedItems("file-content")});
    };

    this.loadFilesInQueue = function(pos)
    {
        this.dragItemType = null;
        ajaxdj_ref.send_post_command('queueAdd&pos='+pos,
            {path: this.getSelectedItems("file-content")});
    };

    this.addToPlaylist = function(name)
    {
        ajaxdj_ref.send_post_command('staticPlaylistAdd',
            {plname: name, path: this.getSelectedItems("file-content")});
    };

    /*************************************/
    /******** Playlist Part ****************/
    /*************************************/
    this.updatePlaylistList = function(playlistList)
    {
        var Items = playlistList.getElementsByTagName("item");
        this.playlistList = new Array();
        for (var i=0;item=Items[i];i++)
            this.playlistList.push(item.firstChild.data);

        // Update fileList Menu
        var menu = $('fileaddplaylist-menu');
        while(menu.hasChildNodes())
            menu.removeChild(menu.firstChild);
        this.contructPlsListMenu(menu,true);

        // Update playlist-save Menu
        var menu = $('playlist-save-plslist');
        while(menu.hasChildNodes())
            menu.removeChild(menu.firstChild);
        this.contructPlsListMenu(menu,false);

        this.constructItemList(playlistList,"playlistList-content");
    };

    this.loadPlaylist = function(pos)
    {
        this.dragItemType = null;
        ajaxdj_ref.send_post_command('playlistLoad&pos='+pos,
            {pls_name: this.getSelectedItems("playlistList-content")});
    };

    this.loadPlaylistInQueue = function(pos)
    {
        this.dragItemType = null;
        ajaxdj_ref.send_post_command('queueLoad&pos='+pos,
            {pls_name: this.getSelectedItems("playlistList-content")});
    };

    this.erasePlaylist = function()
    {
        var rs = window.confirm(ajaxdj_ref.getString("confirm"));

        if (rs)
            ajaxdj_ref.send_post_command('playlistErase',
                {name: this.getSelectedItems("playlistList-content")});
    };

    /*************************************/
    /******** Search Part ****************/
    /*************************************/
    this.searchFile = function()
    {
        var text = $('search-text').value;
        var typ = $('search-type').selectedItem.value;
        ajaxdj_ref.send_post_command("search",{type:typ,txt:text});
    };

    this.searchClear = function()
    {
        $('search-text').value = "";
        ajaxdj_ref.send_post_command('getdir',{dir:this.curDir});
    };


/*********************************************************/
/*************  INTERNAL FUNCTIONS ***********************/
/*********************************************************/
    this.contructPlsListMenu = function(menu,cmd)
    {
        for(var i in this.playlistList) {
            var item = document.createElement("menuitem");
            item.setAttribute("label",this.playlistList[i]);
            if (cmd) {
                item.setAttribute("oncommand",
                "fileList_ref.addToPlaylist('"+this.playlistList[i]+"');");
                }
            menu.appendChild(item);
            }
    };

    this.customConstructDirRow = function(dirItem)
    {
        dirItem.ondblclick = function(e) {
            ajaxdj_ref.send_post_command("getdir",
                { dir:e.target.value }); };
        dirItem.addEventListener('draggesture', FileObserver.dragStart, true);
    };

    this.constructFileRow = function(file)
    {
        var fileName = file.firstChild.data;
        var fileItem = document.createElement("listitem");
        fileItem.setAttribute("label",fileName);
        fileItem.setAttribute("context","fileList-menu");
        fileItem.className = "audio-item listitem-iconic";
        var path = file.getAttribute("path");
        fileItem.setAttribute("value",path);
        fileItem.setAttribute("type","audio-file");
        fileItem.addEventListener('draggesture', FileObserver.dragStart, true);

        return fileItem;
    };

    this.constructPlaylistRow = function(playlist)
    {
        var plsItem = document.createElement("listitem");
        plsItem.setAttribute("label",playlist.firstChild.data);
        plsItem.setAttribute("context","playlistList-menu");
        plsItem.setAttribute("value",playlist.firstChild.data);
        plsItem.setAttribute("type","playlist");
        plsItem.className = "playlist-item listitem-iconic";
        plsItem.addEventListener('draggesture', FileObserver.dragStart, true);

        return plsItem;
    };
};

// heritage by prototype
FileList.prototype = new CommonList;


var FileObserver = {
    dragStart: function (evt)
        {
        evt.stopPropagation();

        try{
            netscape.security.PrivilegeManager.
                enablePrivilege("UniversalXPConnect");
            }
        catch(ex){return}

        fileList_ref.dragItemType = evt.target.getAttribute("type");
        var plainText=evt.target.value;

        var ds = Components.classes["@mozilla.org/widget/dragservice;1"].
               getService(Components.interfaces.nsIDragService);
        var trans = Components.classes["@mozilla.org/widget/transferable;1"].
               createInstance(Components.interfaces.nsITransferable);
        trans.addDataFlavor("text/plain");
        var textWrapper = Components.classes["@mozilla.org/supports-string;1"].
               createInstance(Components.interfaces.nsISupportsString);
        textWrapper.data = plainText;
        trans.setTransferData("text/plain",textWrapper,textWrapper.data.length);
        // create an array for our drag items, though we only have one this time
        var transArray = Components.classes["@mozilla.org/supports-array;1"].
                createInstance(Components.interfaces.nsISupportsArray);
        transArray.AppendElement(trans);
        // Actually start dragging
        ds.invokeDragSession(evt.target, transArray, null,
            ds.DRAGDROP_ACTION_COPY + ds.DRAGDROP_ACTION_MOVE);
        }

    };
// vim: ts=4 sw=4 expandtab
