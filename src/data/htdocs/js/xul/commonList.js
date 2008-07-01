// commonList.js

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


var CommonList = function()
{
    this.curDir = "";
    this.menuId = "";
    this.menuCommand = "";
    this.contextMenuId = "";
    this.listType = "";

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

    this.constructItemList = function(itemList,content)
    {
        var listObj = $(content);
        var currentItem = listObj.firstChild;

        var Items = itemList.getElementsByTagName("item");
        for(var i=0;item=Items.item(i);i++) {
            var type = item.getAttribute("type");
            switch (type) {
                case "song":
                    var row = this.constructFileRow(item);
                    break;
                case "directory":
                    var row = this.constructDirRow(item);
                    break;
                case "playlist":
                    var row = this.constructPlaylistRow(item);
                    break;
                case "video":
                    var row = this.constructVideoRow(item);
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

    this.constructDirRow = function(dir)
    {
        var dirName = dir.firstChild.data;
        var dirItem = document.createElement("listitem");
        dirItem.setAttribute("label",dirName);
        dirItem.setAttribute("type","directory");
        var path = this.curDir != "" ? this.curDir+"/"+dirName : dirName;
        dirItem.setAttribute("value",path);
        dirItem.setAttribute("context",this.contextMenuId);
        dirItem.setAttribute("type","directory");
        dirItem.className = "listitem-iconic directory-item";

        this.customConstructDirRow(dirItem)
        return dirItem;
    };

    this.updateDatabase = function(upObj)
    {
        var progress = upObj.getAttribute("p");
        var upId = upObj.firstChild.data;
        if (progress == "1") {
            $(this.updateBox).selectedIndex = 1
            $('audio-update-progressbar').mode = "undetermined";
            setTimeout(
                "ajaxdj_ref.send_command('"+this.listType+
                "_update_check',{id:"+upId+
                "},false)",1000);
            }
        else {
            $(this.updateBox).selectedIndex = 0
            $('audio-update-progressbar').mode = "determined";
            }
    };

};

// vim: ts=4 sw=4 expandtab
