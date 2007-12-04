// commonTree.js

var CommonTreeManagement = function()
{
    this.treeId = -1;

    this.init = function()
    {
        try{
            netscape.security.PrivilegeManager.
                enablePrivilege("UniversalXPConnect");
            }
        catch(ex){return}

        this.tree.controllers.appendController(this.treeController);
    };

    this.update = function(obj)
    {
        var id = parseInt(obj.getAttribute("id"));
        if (id > this.treeId) {
            this.treeId = id;
            // Update datasources
            this.tree.setAttribute("datasources",window.location.href+"rdf/"+
                this.module+"-"+id+".rdf");

            // do custom update
            this.customUpdate(obj);
            }
    };

    this.removeItems = function()
    {
        var items = this.getTreeSelection();
        ajaxdj_ref.send_post_command(this.module+"Remove", {ids: items});
    };

    this.getTreeSelection = function()
    {
        var start = new Object();
        var end = new Object();
        var numRanges = this.tree.view.selection.getRangeCount();
        var selectedItems = Array();

        for (var t=0; t<numRanges; t++) {
            this.tree.view.selection.getRangeAt(t,start,end);
            for (var v=start.value; v<=end.value; v++) {
                var item = this.tree.contentView.getItemAtIndex(v);
                var str = item.id;
                selectedItems.push(str.split("/")[3]);
                }
            }

        return selectedItems;
    };


    /**************************************************************/
    // Event handler
    /**************************************************************/
    this.play = function()
    {
        if (this.tree.contentView) {
            var item = this.tree.contentView.getItemAtIndex(
                            this.tree.currentIndex);
            var str = item.id;
            ajaxdj_ref.send_command("goto",{ id:str.split("/")[3] },true);
            }
    };

    this.showPopupMenu = function(evt)
    {
        var menu = $(this.module+'-menu');
        menu.hidePopup();

        var childElement = {}, rowObject = {}, columnObject = {};
        this.tree.treeBoxObject.getCellAt(evt.clientX, evt.clientY, rowObject,
            columnObject, childElement);

        if (rowObject.value == -1)
            return;

        var context_x = evt.clientX + 5;
        var context_y = evt.clientY;
        menu.showPopup(this.tree,context_x,context_y,"context",
            null,null,null);
    };

    /**************************************************************/
    // Drag and Drop support
    /**************************************************************/
    this.row = {obj: null, pos: -1};

    this.dragFileExit = function(evt)
    {
        evt.target.className = "";
    };

    this.dragOver = function(evt)
    {
        evt.stopPropagation();

        try{
            netscape.security.PrivilegeManager.
                enablePrivilege("UniversalXPConnect");
            }
        catch(ex){return}

        var oldRow = this.row.obj;
        var row = this.tree.treeBoxObject.getRowAt(evt.pageX, evt.pageY)
        if (this.tree.view && row >= 0) {
            var item = this.tree.contentView.getItemAtIndex(row);
            this.row.obj = item.firstChild;
            this.row.pos = row;
            this.row.obj.setAttribute("properties","dragged");
            if (oldRow && oldRow != this.row.obj){
                oldRow.setAttribute("properties","");
                }
            }
        else {
            this.row.pos = -1;
            if (oldRow) {
                try{ oldRow.setAttribute("properties","");}
                catch(ex){}
                }
            }

        var dragService = Components
            .classes["@mozilla.org/widget/dragservice;1"].
            getService().QueryInterface(Components.interfaces.nsIDragService);
        if (dragService) {
            var dragSession = dragService.getCurrentSession();
            if (dragSession)
                dragSession.canDrop = true;
            }
    };

    this.dragEnter = function(evt)
    {
        evt.stopPropagation();

        try{
            netscape.security.PrivilegeManager.
                enablePrivilege("UniversalXPConnect");
            }
        catch(ex){return}

        var dragService = Components
            .classes["@mozilla.org/widget/dragservice;1"].
            getService().QueryInterface(Components.interfaces.nsIDragService);
        if (dragService)
        {
            var dragSession = dragService.getCurrentSession();
            if (dragSession)
                dragSession.canDrop = true;
        }
    };

    this.dragExit = function(evt)
    {
        evt.stopPropagation();

        try{
            netscape.security.PrivilegeManager.
                enablePrivilege("UniversalXPConnect");
            }
        catch(ex){return}

        if (this.row.obj) {
            this.row.pos = -1;
            try{ this.row.obj.setAttribute("properties","");}
            catch(ex){}
            }

        var dragService = Components
            .classes["@mozilla.org/widget/dragservice;1"].
            getService().QueryInterface(Components.interfaces.nsIDragService);
        if (dragService) {
            var dragSession = dragService.getCurrentSession();
            if (dragSession)
                dragSession.canDrop = false;
            }
    };

    this.drop = function(evt)
    {
        try{
            netscape.security.PrivilegeManager.
                enablePrivilege("UniversalXPConnect");
            }
        catch(ex){return}

        evt.stopPropagation();

        if (this.row.obj) {
            try{ this.row.obj.setAttribute("properties","");}
            catch(ex){}
            }

        this.dropAction(this.row.pos);
    };
};
