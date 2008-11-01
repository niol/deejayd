/* Deejayd, a media player daemon
# Copyright (C) 2007-2008 Mickael Royer <mickael.royer@gmail.com>
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


var _Source = function()
{
    this.treeId = -1;
    this.playing = null;
    this.treeBuilder = null;
    this.dropSupport = true;

    this.init = function()
    {
        if (typeof this.treeController == 'object') {
            netscape.security.PrivilegeManager.
                enablePrivilege("UniversalXPConnect");
            this.tree.controllers.appendController(this.treeController);
            }
        if (this.dropSupport) {
            this.dropSupport = new TreeDropSupport(this.tree, this.dropAction,
                this.supportedDropData);
            }
    };

    this.update = function(obj)
    {
        var id = parseInt(obj.getAttribute("id"));
        if (id != this.treeId) {
            this.treeId = id;

            netscape.security.PrivilegeManager.
                enablePrivilege("UniversalXPConnect");
            // Update datasources
            var RDF = Components.classes["@mozilla.org/rdf/rdf-service;1"].
                getService(Components.interfaces.nsIRDFService);
            var ds = RDF.GetDataSource(window.location.href+"rdf/"+
                this.module+"-"+id+".rdf");

            var currentSources = this.tree.database.GetDataSources();
            while (currentSources.hasMoreElements()) {
                var src = currentSources.getNext();
                this.tree.database.RemoveDataSource(src);
                }
            this.tree.database.AddDataSource(ds);
            this.tree.builder.rebuild();

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

    this.goToCurSong = function()
    {
        if (this.playing != null) {
            var boxobject = this.tree.treeBoxObject;
            boxobject.ensureRowIsVisible(this.playing["pos"]);
            }
    };

    this.updatePlaylistList = function(playlistList)
    {
        updatePlaylistMenu(this.module+"-pls-menu", playlistList, this.ref);
    };

    this.addToPlaylist = function(pl_id)
    {
        var items = this.getTreeSelection("value");
        ajaxdj_ref.send_post_command('staticPlaylistAdd',
            {pl_id: pl_id, values: items, type: 'id'});
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
        try { var item = this.tree.contentView.getItemAtIndex(parseInt(pos)) }
        catch (ex) { // tree not ready
            var cmd = this.ref+'.setPlaying('+pos+','+id+',"'+state+'")';
            setTimeout(cmd,300);
            return;
            }

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
    // drop support
    /**************************************************************/
    this.dragOver = function(evt)
    {
        if (this.dropSupport) { this.dropSupport.dragOver(evt); }
    }

    this.dragEnter = function(evt)
    {
        if (this.dropSupport) { this.dropSupport.dragEnter(evt); }
    }

    this.dragExit = function(evt)
    {
        if (this.dropSupport) { this.dropSupport.dragExit(evt); }
    }

    this.drop = function(evt)
    {
        if (this.dropSupport) { this.dropSupport.drop(evt); }
    }
};

var TreeBuilderObserver = function(source)
{
    this.source = source;
    this.item = null;

    this.willRebuild = function(builder)
    {
        var tree = this.source.tree;
        if (tree.currentIndex != -1) {
            this.item = tree.contentView.getItemAtIndex(tree.currentIndex);
            }
        else { this.item = null; }
    };

    this.didRebuild = function(builder)
    {
        // update playing
        if (this.source.playing != null)
            this.source.setPlaying(this.source.playing["pos"],
                this.source.playing["id"], this.source.playing["state"]);

        // set previous selection
        if (this.item) {
            alert(this.item);
            var tree = this.source.tree;
            var idx = tree.contentView.getIndexOfItem(item);
            if (idx != -1) tree.view.selection.select(idx);
            }
    };
};

// vim: ts=4 sw=4 expandtab
