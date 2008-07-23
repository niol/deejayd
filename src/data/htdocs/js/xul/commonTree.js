// commonTree.js

var CommonTreeManagement = function()
{
    this.treeId = -1;
    this.playing = null;

    this.init = function()
    {
        try{
            netscape.security.PrivilegeManager.
                enablePrivilege("UniversalXPConnect");
            }
        catch(ex){return}

        if (typeof this.treeController == 'object')
            this.tree.controllers.appendController(this.treeController);
    };

    this.update = function(obj)
    {
        var id = parseInt(obj.getAttribute("id"));
        if (id != this.treeId) {
            this.treeId = id;
            // clear selection
            if (this.tree.view) { this.tree.view.selection.clearSelection(); }
            // Update datasources
            this.tree.setAttribute("datasources",window.location.href+"rdf/"+
                this.module+"-"+id+".rdf");
            // do custom update
            this.customUpdate(obj);
            // update playing
            if (this.playing != null)
                this.setPlaying(this.playing["pos"], this.playing["id"],
                    this.playing["state"]);
            }
    };

    this.removeItems = function()
    {
        var items = this.getTreeSelection("id");
        ajaxdj_ref.send_post_command(this.module+"Remove", {ids: items});
    };

    this.getTreeSelection = function(type)
    {
        var start = new Object();
        var end = new Object();
        var numRanges = this.tree.view.selection.getRangeCount();
        var selectedItems = Array();

        for (var t=0; t<numRanges; t++) {
            this.tree.view.selection.getRangeAt(t,start,end);
            for (var v=start.value; v<=end.value; v++) {
                var item = this.tree.contentView.getItemAtIndex(v);
                var str = item.getAttribute(type);
                if (type == "id")
                    selectedItems.push(str.split("/")[3]);
                else
                    selectedItems.push(str);
                }
            }

        return selectedItems;
    };

    this.setRating = function(rating)
    {
        var items = this.getTreeSelection("value");
        var t = this.module == "video" ? "video" : "audio";
        ajaxdj_ref.send_post_command("setMediaRating", {ids: items, type: t,
                                                        value: rating});
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
        menu.openPopup(null , "",context_x,context_y,true,false);
    };

    this.setPlaying = function(pos, id, state)
    {
        if (!this.tree.contentView) { // tree not ready
            var cmd = this.ref+'.setPlaying('+pos+','+id+',"'+state+'")';
            setTimeout(cmd,500);
            return;
            }
        var item = this.tree.contentView.getItemAtIndex(parseInt(pos))
        if (item) {
            // get id of item
            var item_id = item.id;
            item_id = item_id.split("/")[3];
            if (item_id != id) // not the right row
                return;

            this.playing = {"pos": pos, "id": id, "state": state};
            this.playing["row"] = item.firstChild;
            this.playing["row"].setAttribute("properties", state);
            this.playing["cell"] = this.playing["row"].firstChild;
            this.playing["cell"].setAttribute("properties", state);
            }
    };

    this.updatePlaying = function(state)
    {
        if (this.playing) {
            this.playing['cell'].setAttribute("properties", state);
            this.playing['row'].setAttribute("properties", state);
            this.playing["state"] = state;
            }
    };

    this.resetPlaying = function()
    {
        if (this.playing) {
            this.playing["cell"].setAttribute("properties", "");
            this.playing["row"].setAttribute("properties", "");
            this.playing = null;
            }
    };

    this.setPlayorder = function()
    {
        var val = $(this.module + '-playorder').value;
        ajaxdj_ref.send_post_command("playorder",
            {value:val,source:this.module});
    };

    /**************************************************************/
    // Drag and Drop support
    /**************************************************************/
    this.row = {obj: null, pos: -1};

    this.dragFileExit = function(evt) { evt.target.className = ""; };

    this.getDragData = function(dragSession)
    {
        if (dragSession.isDataFlavorSupported("text/unicode")
               && dragSession.numDropItems == 1) {
            var trans = Components.
                classes["@mozilla.org/widget/transferable;1"].
                createInstance(Components.interfaces.nsITransferable);
            trans.addDataFlavor("text/unicode");
            dragSession.getData(trans, 0);

            var len = {};
            var data = {};
            try {
                trans.getTransferData("text/unicode", data, len);
                var result = data.value.QueryInterface(
                    Components.interfaces.nsISupportsString);
                return result.data;
                }
            catch(ex){return false}
            }
        return false;
    };

    this.supportedDropData = Array();
    this.isDataCanDrop = function(dragSession)
    {
        var data = this.getDragData(dragSession);
        if (data) {
            for (var i in this.supportedDropData) {
                if (data == this.supportedDropData[i])
                    return true;
                }
            }
        return false;
    };

    this.dragStart = function(evt)
    {
        evt.stopPropagation();
        try{
            netscape.security.PrivilegeManager.
                enablePrivilege("UniversalXPConnect");
            }
        catch(ex){return} // drag and drop not allowed

        // set drag session
        var ds = Components.classes["@mozilla.org/widget/dragservice;1"].
               getService(Components.interfaces.nsIDragService);

        // build object to carry in this drag session
        var trans = Components.classes["@mozilla.org/widget/transferable;1"].
               createInstance(Components.interfaces.nsITransferable);
        trans.addDataFlavor("text/unicode");
        var textWrapper = Components.classes["@mozilla.org/supports-string;1"].
               createInstance(Components.interfaces.nsISupportsString);
        textWrapper.data = this.module;
        trans.setTransferData("text/unicode",textWrapper,this.module.length*2);

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

        var dragService = Components
            .classes["@mozilla.org/widget/dragservice;1"].
            getService().QueryInterface(Components.interfaces.nsIDragService);
        if (dragService) {
            var dragSession = dragService.getCurrentSession();
            if (!dragSession) { return; }
            dragSession.canDrop = this.isDataCanDrop(dragSession);
            }

        if (dragSession.canDrop) {
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
            if (dragSession)
                dragSession.canDrop = this.isDataCanDrop(dragSession);
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

        var dragService = Components
            .classes["@mozilla.org/widget/dragservice;1"].
            getService().QueryInterface(Components.interfaces.nsIDragService);
        if (dragService) {
            var dragSession = dragService.getCurrentSession();
            if (dragSession) { var data = this.getDragData(dragSession); }
            if (!dragSession || !data) { return; }
            }
        if (this.row.obj) {
            try{ this.row.obj.setAttribute("properties","");}
            catch(ex){}
            }

        this.dropAction(this.row.pos, data);
    };
};
