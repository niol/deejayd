// commonTree.js

var CommonTreeManagement = function()
{
    this.treeId = -1;
    this.canDrop = false;
    this.mediaDragged = false;

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

    this.dragFileExit = function(evt) { evt.target.className = ""; };

    this.dragStart = function(evt)
    {
        evt.stopPropagation();
        if (!this.canDrop)
            return;
        try{
            netscape.security.PrivilegeManager.
                enablePrivilege("UniversalXPConnect");
            }
        catch(ex){return} // drag and drop not allowed

        this.mediaDragged = true;
        var ds = Components.classes["@mozilla.org/widget/dragservice;1"].
               getService(Components.interfaces.nsIDragService);
        var trans = Components.classes["@mozilla.org/widget/transferable;1"].
               createInstance(Components.interfaces.nsITransferable);
        trans.addDataFlavor("text/plain");
        var textWrapper = Components.classes["@mozilla.org/supports-string;1"].
               createInstance(Components.interfaces.nsISupportsString);
        textWrapper.data = "";
        trans.setTransferData("text/plain",textWrapper,textWrapper.data.length);
        // create an array for our drag items, though we only have one this time
        var transArray = Components.classes["@mozilla.org/supports-array;1"].
                createInstance(Components.interfaces.nsISupportsArray);
        transArray.AppendElement(trans);
        // Actually start dragging
        ds.invokeDragSession(evt.target, transArray, null,
            ds.DRAGDROP_ACTION_COPY + ds.DRAGDROP_ACTION_MOVE);
    };

    this.dragOver = function(evt)
    {
        evt.stopPropagation();
        try{
            netscape.security.PrivilegeManager.
                enablePrivilege("UniversalXPConnect");
            }
        catch(ex){return} // drag and drop not allowed

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
            if (dragSession && (this.mediaDragged || fileList_ref.dragItemType))
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
        catch(ex){return} // drag and drop not allowed

        var dragService=Components.classes["@mozilla.org/widget/dragservice;1"].
            getService().QueryInterface(Components.interfaces.nsIDragService);
        if (dragService) {
            var dragSession = dragService.getCurrentSession();
            if (dragSession && (this.mediaDragged || fileList_ref.dragItemType))
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
        catch(ex){return} // drag and drop not allowed

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
        evt.stopPropagation();
        try{
            netscape.security.PrivilegeManager.
                enablePrivilege("UniversalXPConnect");
            }
        catch(ex){return} // drag and drop not allowed

        if (this.row.obj) {
            try{ this.row.obj.setAttribute("properties","");}
            catch(ex){}
            }

        this.dropAction(this.row.pos);
    };
};
