/* Deejayd, a media player daemon
# Copyright (C) 2007-2009 Mickael Royer <mickael.royer@gmail.com>
#                         Alexandre Rossi <alexandre.rossi@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA. */


//
//Common functions
//
function dragStart(evt, data)
{
    evt.stopPropagation();
    netscape.security.PrivilegeManager.
        enablePrivilege("UniversalXPConnect");

    // set drag session
    var ds = Components.classes["@mozilla.org/widget/dragservice;1"].
           getService(Components.interfaces.nsIDragService);

    // build object to carry in this drag session
    var trans = Components.classes["@mozilla.org/widget/transferable;1"].
           createInstance(Components.interfaces.nsITransferable);
    trans.addDataFlavor("text/unicode");
    var textWrapper = Components.classes["@mozilla.org/supports-string;1"].
           createInstance(Components.interfaces.nsISupportsString);
    textWrapper.data = data;
    trans.setTransferData("text/unicode",textWrapper,data.length*2);

    // create an array for our drag items, though we only have one this time
    var transArray = Components.classes["@mozilla.org/supports-array;1"].
            createInstance(Components.interfaces.nsISupportsArray);
    transArray.AppendElement(trans);

    // Actually start dragging
    ds.invokeDragSession(evt.target, transArray, null,
        ds.DRAGDROP_ACTION_COPY + ds.DRAGDROP_ACTION_MOVE);
};

//
//Tree drag and drop
//
var TreeDropSupport = function(tree, drop_action, supportedDropData)
{
    this.tree = tree;
    this.dropAction = drop_action;
    this.supportedDropData = supportedDropData;

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

    this.dragOver = function(evt)
    {
        evt.stopPropagation();
        netscape.security.PrivilegeManager.
            enablePrivilege("UniversalXPConnect");

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
        netscape.security.PrivilegeManager.
            enablePrivilege("UniversalXPConnect");

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
        netscape.security.PrivilegeManager.
            enablePrivilege("UniversalXPConnect");

        if (this.row.obj) {
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
        netscape.security.PrivilegeManager.
            enablePrivilege("UniversalXPConnect");

        var dragService = Components
            .classes["@mozilla.org/widget/dragservice;1"].
            getService().QueryInterface(Components.interfaces.nsIDragService);
        if (dragService) {
            var dragSession = dragService.getCurrentSession();
            if (dragSession) { var data = this.getDragData(dragSession); }
            if (!dragSession || !data) { return false; }
            }
        if (this.row.obj) {
            try{ this.row.obj.setAttribute("properties","");}
            catch(ex){}
            }

        this.dropAction(this.row.pos, data);
        return false;
    };
}

// vim: ts=4 sw=4 expandtab
