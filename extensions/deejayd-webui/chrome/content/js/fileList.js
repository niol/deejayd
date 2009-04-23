// fileList.js

// listbox.selectAll function does not work correctly.
// this (awful) hack is needed
var slAll = function(content) {
    var list = $(content);
    var nb =  list.getNumberOfVisibleRows();

    list.clearSelection();
    var i = 0;
    while (i< list.getRowCount()) {
        list.ensureIndexIsVisible(i);
        i += nb;
        }
    list.ensureIndexIsVisible(list.getRowCount()-2);
    list.selectAll();
};

var fileList_ref;

var FileList = function()
{
    fileList_ref = this;
    this.curDir = "";
    this.menuId = "navigation-path";
    this.menuCommand = "getdir";
    this.contextMenuId = "fileList-menu";
    this.listType = "audio";
    this.dragFunc = function (evt) {
        var plainText = evt.target.getAttribute("type") + "-list";
        dragStart(evt, plainText);
        };

    this.init = function()
    {
        netscape.security.PrivilegeManager.
            enablePrivilege("UniversalXPConnect");
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

    this.constructMenu = function(path)
    {
        var navMenu = $(this.menuId);
        this.eraseMenu(navMenu);
        if (path == '' || !path) {
            navMenu.style.display="none";
            return;
            }

        var tmp = path.split("/");
        for (var i=-1; i < (tmp.length); i++) {
            var tmp_path = '';
            for (var j=0; j<(i); j++)
                tmp_path += tmp[j]+"/";
            tmp_path += (i == -1 ? '' : tmp[i]);

            var button = document.createElement('toolbarbutton');
            var name = tmp[i] ? tmp[i] : 'Root';
            button.setAttribute("crop","end");
            button.setAttribute("label",name);
            button.setAttribute("tooltiptext",name);
            button.id = tmp_path ? tmp_path : 'root_link';

            button.addEventListener('command', this.getDir, true);

            navMenu.appendChild(button);
            }
        navMenu.style.display="block";
    };

    this.getDir = function(e)
    {
        var args = {};
        if (this.id !='root_link')
            args['dir'] = this.id;
        ajaxdj_ref.send_post_command(this.menuCommand,args);
    };

    this.eraseMenu = function(navMenu)
    {
        while (navMenu.hasChildNodes())
            navMenu.removeChild(navMenu.firstChild);
    };

    this.updateDatabase = function(progress)
    {
        if (progress == "1") {
            $("audio-update").selectedIndex = 1
            $('audio-update-progressbar').mode = "undetermined";
            }
        else {
            $("audio-update").selectedIndex = 0
            $('audio-update-progressbar').mode = "determined";
            }
    };

    this.getSelectedItems = function(content)
    {
        var navList = $(content);
        var items = navList.selectedItems;
        var argArray = new Array();
        for (var id in items) {
            var item = items[id];
            argArray.push(item.value);
            }

        return argArray;
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

    this.__getSelectedType = function(id)
    {
        var navList = $(id);
        var items = navList.selectedItems;
        try { var type = items[0].getAttribute("value_type"); }
        catch(ex) {
            var type = "path";
            }
        return type;
    };

    this.loadFiles = function(pos)
    {
        ajaxdj_ref.send_post_command('playlistAdd&pos='+pos,
            {values: this.getSelectedItems("file-content"),
             type: this.__getSelectedType("file-content")});
    };

    this.loadFilesInQueue = function(pos)
    {
        ajaxdj_ref.send_post_command('queueAdd&pos='+pos,
            {values: this.getSelectedItems("file-content"),
             type: this.__getSelectedType("file-content")});
    };

    this.addToPlaylist = function(pl_id)
    {
        ajaxdj_ref.send_post_command('staticPlaylistAdd',
            {pl_id: pl_id, values: this.getSelectedItems("file-content"),
             type: this.__getSelectedType("file-content")});
    };

    /*************************************/
    /******** Playlist Part ****************/
    /*************************************/
    this.updatePlaylistList = function(playlistList)
    {
        updatePlaylistMenu('fileaddplaylist-menu',playlistList,"fileList_ref");
        updatePlaylistMenu('playlist-save-plslist',playlistList,"fileList_ref");

        this.constructItemList(playlistList,"playlistList-content");
    };

    this.loadPlaylist = function(pos)
    {
        ajaxdj_ref.send_post_command('playlistLoad&pos='+pos,
            {pls_ids: this.getSelectedItems("playlistList-content")});
    };

    this.loadPlaylistInQueue = function(pos)
    {
        ajaxdj_ref.send_post_command('queueLoad&pos='+pos,
            {pls_ids: this.getSelectedItems("playlistList-content")});
    };

    this.erasePlaylist = function()
    {
        var rs = window.confirm(ajaxdj_ref.getString("confirm"));

        if (rs)
            ajaxdj_ref.send_post_command('playlistErase',
                {pl_ids: this.getSelectedItems("playlistList-content")});
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
                "fileList_ref.addToPlaylist('"+this.playlistList[i].id+"');");
                }
            menu.appendChild(item);
            }
    };

    this.constructItemList = function(itemList,content)
    {
        var listObj = $(content);
        var currentItem = listObj.firstChild;

        var Items = itemList.getElementsByTagName("item");
        for(var i=0;item=Items.item(i);i++) {
            var type = item.getAttribute("type");
            switch (type) {
                case "song":
                    var row = this.__constructRow({label: item.firstChild.data,
                        value: item.getAttribute("value"),type:"audio-file",
                        value_type: item.getAttribute("value_type"),
                        context: "fileList-menu"});
                    row.className = "audio-item listitem-iconic";
                    break;
                case "directory":
                    var dirName = item.firstChild.data;
                    var path = this.curDir != "" ?
                        this.curDir+"/"+dirName : dirName;
                    var row = this.__constructRow({label: dirName,
                        value: path, value_type: "path", type: "directory",
                        context: this.contextMenuId});
                    row.className = "listitem-iconic directory-item";
                    row.ondblclick = function(e) {
                        ajaxdj_ref.send_post_command("getdir",
                            { dir:e.target.value }); };
                    break;
                case "playlist":
                    var row = this.__constructRow({label: item.firstChild.data,
                        value: item.getAttribute("id"),type:"playlist",
                        context: "playlistList-menu"});
                    row.className = item.getAttribute("pls_type")+
                        "-playlist-item listitem-iconic";
                    break;
                }

            if (currentItem) {
                listObj.replaceChild(row,currentItem);
                currentItem = row.nextSibling;
                }
            else
                listObj.appendChild(row);
            }

        while(currentItem) {
            var nextItem = currentItem.nextSibling;
            listObj.removeChild(currentItem);
            currentItem = nextItem;
            }
    };

    this.__constructRow = function(row, type)
    {
        var item = document.createElement("listitem");
        item.setAttribute("type",type);
        for (key in row) { item.setAttribute(key, row[key]); }
        item.addEventListener('draggesture', this.dragFunc, true);

        return item;
    };
};

// vim: ts=4 sw=4 expandtab
