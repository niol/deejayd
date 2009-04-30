// fileList.js

var panel_ref;
var Panel = function()
{
    panel_ref = this;
    this.ref = "panel_ref";
    this.dropSupport = false;

    this.module = "panel";
    this.tree = $("panel-tree");
    this.selected_playlist = null;
    this.selected_mode = null;
    // Activate this mode
    $("panel-source").hidden = false;
    this.selectedIdx = {};

    this.treeController = false;

    this.initPanelTags = function(obj)
    {
        var av_tags = new Array("genre","artist","various_artist","album");
        var tags = obj.getElementsByTagName("tag");
        for (var i=0; tag = tags.item(i); i++) {
            for(j=0;j<av_tags.length;j++)
                if(tag.firstChild.data==av_tags[j]) av_tags.splice(j, 1);
            }
        // hide not used panel
        for (idx in av_tags) {
            var tag_list = $(av_tags[idx] + "-panel");
            tag_list.hidden = true;
            }
    };

    this.__setPanel = function(panel)
    {
        $('panel-select-button').checked = panel;
        $('filter-box').hidden = !panel;
        $('panel-box').hidden = !panel;
        this.selected_playlist = null;
        this.selected_mode = panel ? "panel" : "panel-playlist";
    };

    this.updatePanel = function(obj)
    {
        var list = obj.getElementsByTagName("item");
        var tag = obj.getAttribute("tag");
        var pn = $(tag+"-panel");
        // remove listener
        try { pn.removeEventListener("select", panelSelectObserver, false); }
        catch (ex) {}
        // remove old item
        pn.clearSelection();
        while(pn.getRowCount() > 0) { pn.removeItemAt(0); }

        this.selectedIdx[tag] = new Array();
        for (var i=0; item = list[i]; i++) {
            var listitem = pn.appendItem(item.getAttribute("label"),
                    item.getAttribute("value"));
            if (item.getAttribute("selected") == "true") {
                this.selectedIdx[tag].push(i);
                }
            }
        setTimeout("panel_ref.setPanelSelection('"+tag+"');",100);
    }

    this.setPanelSelection = function(tag)
    {
        var pn = $(tag+"-panel");
        for (j in this.selectedIdx[tag]) {
            pn.ensureIndexIsVisible(this.selectedIdx[tag][j]);
            var listitem = pn.getItemAtIndex(this.selectedIdx[tag][j]);
            pn.addItemToSelection(listitem);
            }

        // add listener
        pn.addEventListener("select", panelSelectObserver, false);
    };

    // try to update panel in another thread do not work for now
    /*this.updatePanel = function(obj)
    {
        var main = Components.classes["@mozilla.org/thread-manager;1"].
            getService().mainThread;
        var background = Components.classes["@mozilla.org/thread-manager;1"].
            getService().newThread(0);
        background.dispatch(new panelBuild(main, obj),
                background.DISPATCH_NORMAL);
    };*/

    this.update = function(obj)
    {
        var id = parseInt(obj.getAttribute("id"));
        if (id != this.treeId) {
            this.treeId = id;

            // first scroll to top
            var boxobject = this.tree.treeBoxObject;
            boxobject.ensureRowIsVisible(0);

            netscape.security.PrivilegeManager.
                enablePrivilege("UniversalXPConnect");
            var RDF = Components.classes["@mozilla.org/rdf/rdf-service;1"].
                getService(Components.interfaces.nsIRDFService);
            var ds = RDF.GetDataSource(ajaxdj_ref.url+"rdf/"+
                "panel"+"-"+this.treeId+".rdf");

            var pls_tree = $('panel-pls-list');
            pls_tree.view.selection.clearSelection();
            var mode = obj.getAttribute("type");
            if (mode == "playlist") {
                this.__setPanel(false);

                // select current playlist
                var items = pls_tree.getElementsByTagName("treerow");
                for (var i=0; item=items[i]; i++) {
                    if (item.getAttribute("value") ==
                            obj.getAttribute("value")){
                        pls_tree.view.selection.select(i);
                        break;
                        }
                    }
                this.selected_playlist = obj.getAttribute("value");
                }
            else if (mode == "panel") {
                this.__setPanel(true);

                // update filter bar
                $('panel-filter-text').value=
                    obj.getAttribute("filtertext_text");
                $('panel-filter-type').value=
                    obj.getAttribute("filtertext_type");

                // update sort
                var cols = this.tree.getElementsByTagName("treecol");
                for (var i=0; col = cols.item(i); i++) {
                    col.setAttribute("sortActive", "false");
                    col.setAttribute("sortDirection", "");
                    }
                }

            // update sorts
            var sorts = obj.getElementsByTagName("sorts").item(0);
            if (sorts) {
                var sort_items = sorts.getElementsByTagName("item")
                for (var i=0; item = sort_items.item(i); i++) {
                    var col = $("panel-"+item.getAttribute("tag"));
                    col.setAttribute("sortActive", "true");
                    col.setAttribute("sortDirection",
                            item.getAttribute("direction"));
                    }
                }

            var currentSources = this.tree.database.GetDataSources();
            while (currentSources.hasMoreElements()) {
                var src = currentSources.getNext();
                this.tree.database.RemoveDataSource(src);
                }
            this.tree.database.AddDataSource(ds);
            this.tree.builder.rebuild();

            $("panel-description").value = obj.getAttribute("description");
            // update playing
            if (this.playing != null)
                this.setPlaying(this.playing["pos"], this.playing["id"],
                    this.playing["state"]);
            }
    };

    this.updateDatabase = function(progress)
    {
        if (progress == "1") {
            $("panel-audio-update").selectedIndex = 1
            $('panel-audio-update-progressbar').mode = "undetermined";
            }
        else {
            $("panel-audio-update").selectedIndex = 0
            $('panel-audio-update-progressbar').mode = "determined";
            }
    };

    this.updatePlaylistList = function(playlistList)
    {
        updatePlaylistMenu(this.module+"-pls-menu", playlistList, this.ref);

        var tree = $("panel-pls-list");
        var tree_children = $("panel-pls-list-children");
        // first Erase the playlist list
        while(tree_children.hasChildNodes()){
            tree_children.removeChild(tree_children.firstChild);
            }

        // insert new playlist
        var Items = playlistList.getElementsByTagName("item");
        var selected_index = -1;
        for (var i=0;playlist=Items[i];i++) {
            var plsItem = document.createElement("treeitem");
            plsItem.setAttribute("value",playlist.getAttribute("id"));
            plsItem.setAttribute("pls-type",playlist.getAttribute("pls_type"));
            var plsRow = document.createElement("treerow");
            plsRow.setAttribute("value",playlist.getAttribute("id"));
            plsRow.setAttribute("pls-type",playlist.getAttribute("pls_type"));

            var cell = document.createElement("treecell");
            cell.setAttribute("label",playlist.firstChild.data);
            cell.setAttribute("properties",
                    playlist.getAttribute("pls_type")+"-playlist-item");
            plsRow.appendChild(cell);

            plsItem.appendChild(plsRow);
            tree_children.appendChild(plsItem);

            if (playlist.getAttribute("id") == this.selected_playlist)
                selected_index = i;
            }
        // reselect current playlist
        if (selected_index != -1) {tree.view.selection.select(selected_index);}
    };

    this.updatePanelFilter = function(tag)
    {
        var listbox = $(tag+"-panel");
        var values = new Array();
        for (var i=0; item = listbox.getSelectedItem(i); i++)
            values.push(item.getAttribute("value"))
        ajaxdj_ref.send_post_command('panelUpdateFilter',
                {"tag": tag, "values": values});
    };

    this.updatePanelFilterText = function()
    {
        var tag = $("panel-filter-type").value;
        var value = $("panel-filter-text").value;
        ajaxdj_ref.send_post_command('panelUpdateSearch',
            {"tag": tag, "value": value});
    };

    this.clearPanelFilterText = function()
    {
        $("panel-filter-text").value = "";
        this.updatePanelFilterText();
    };

    this.updateSort = function(tag)
    {
        var pn_col = $('panel-'+tag);
        var direction = "ascending";
        if (pn_col.getAttribute("sortActive") == "true"
                && pn_col.getAttribute("sortDirection") == "ascending")
            direction = "descending";
        else if (pn_col.getAttribute("sortActive") == "true"
                && pn_col.getAttribute("sortDirection") == "descending")
            direction = "none";
        ajaxdj_ref.send_post_command('panelSort',
            {"tag": tag, "direction": direction});
    };

    this.loadInQueue = function(pos)
    {
        var items = this.getTreeSelection("value");
        ajaxdj_ref.send_post_command("queueAdd", {"values": items, type: "id",
                                                  "pos": pos});
    };

    this.__playlistPrompt = function(string1, string2)
    {
        var prompts =
            Components.classes["@mozilla.org/embedcomp/prompt-service;1"]
            .getService(Components.interfaces.nsIPromptService);
        var input = {value: ""};
        var check = {value: ""};
        var result = prompts.prompt(window,
                ajaxdj_ref.getString(string1),
                ajaxdj_ref.getString(string2), input, null, check);
        if (result && input.value != "") { return input.value; }
        return null;
    };

    this.createStaticPlaylist = function()
    {
        var pls_name = this.__playlistPrompt("newStaticPls", "enterPlsName");
        if (pls_name) {
            ajaxdj_ref.send_post_command("playlistCreate",
                    {"name": pls_name, type: "static"});
            }
    };

    this.createMagicPlaylist = function()
    {
        var pls_name = this.__playlistPrompt("newMagicPls", "enterPlsName");
        if (pls_name) {
            var params = {input: null, output: null,
                title: ajaxdj_ref.getFormattedString("magicPlsFilters",
                        [pls_name])};
            window.openDialog(
                    'chrome://deejayd-webui/content/playlist-dialog.xul',
                    'playlist-dialog', 'chrome, dialog, modal, resizable=yes',
                    params).focus();
            if (params.output) {
                // record magic playlist
                ajaxdj_ref.send_post_command("playlistCreate",
                    {"name": pls_name, type: "magic", infos: params.output});
                }
            }
    };

    this.editMagicPlaylist = function(pls_id, filters)
    {
        var params = {input: filters, output: null, title: null};
        window.openDialog(
                'chrome://deejayd-webui/content/playlist-dialog.xul',
                'playlist-dialog', 'chrome, dialog, modal, resizable=yes',
                params).focus();
        if (params.output) {
            // record magic playlist
            ajaxdj_ref.send_post_command("magicPlaylistUpdate",
                {"pl_id": pls_id, infos: params.output});
            }
    };

    // drop support for pls list
    this.plsDropSupport = new TreeDropSupport($('panel-pls-list'),
        function(pos, data) {
            if (pos == -1) { return; } // no playlist selected

            var pls = $('panel-pls-list').contentView.getItemAtIndex(pos);
            if (pls.getAttribute("pls-type") == 'magic' ||
                panel_ref.selected_playlist == pls.getAttribute("value"))
                return;

            if (data == 'panel') {
                var items = panel_ref.getTreeSelection("value");
                }
            else if (data == 'queue') {
                var items = queue_ref.getTreeSelection("value");
                }
            ajaxdj_ref.send_post_command('staticPlaylistAdd',
                {pl_id: pls.getAttribute("value"), values: items, type: 'id'});
            },
        Array('panel', 'queue'));
};
// heritage by prototype
Panel.prototype = new _Source;

var PlsPanelObserver = {
    __clearMenu: function() {
         var menu = $("panel-pls-action-menu");
         while(menu.hasChildNodes())
             menu.removeChild(menu.firstChild);
         },
    __buildMenuItem: function(menu)
         {
             var obj = document.createElement("menuitem");
             obj.setAttribute("class", "menuitem-iconic " + menu.cls);
             obj.setAttribute("label", ajaxdj_ref.getString(menu.label));
             obj.setAttribute("oncommand", menu.command);

             $("panel-pls-action-menu").appendChild(obj);
         },
    updateMenu: function (evt)
        {
            // first remove old menuitem
            this.__clearMenu();
            var tree = $('panel-pls-list');
            var childElement = {}, rowObject = {}, columnObject = {};
            tree.treeBoxObject.getCellAt(evt.clientX, evt.clientY, rowObject,
                columnObject, childElement);

            if (columnObject.value && rowObject.value != -1) {
                var item = tree.contentView.getItemAtIndex(rowObject.value);
                if (item.getAttribute("pls-type") == "magic")
                    this.__buildMenuItem({label: "edit", cls: "edit-action",
                        command: "ajaxdj_ref.send_post_command("+
                            "'magicPlaylistEdit',{pl_id: "+
                            item.getAttribute("value")+"}, true);"});
                this.__buildMenuItem({label: "remove", cls: "remove-action",
                    command: "PlsPanelObserver.removePlaylist('"+
                    item.getAttribute("value")+"');"});
                }
            else {
                this.__buildMenuItem({label: "newStaticPls",
                    cls: "playlist-new",
                    command: "panel_ref.createStaticPlaylist();"});
                this.__buildMenuItem({label: "newMagicPls",
                    cls: "playlist-new",
                    command: "panel_ref.createMagicPlaylist();"});
                }
        },
    setPlaylist: function (evt)
        {
            var tree = $('panel-pls-list');
            var childElement = {}, rowObject = {}, columnObject = {};
            tree.treeBoxObject.getCellAt(evt.clientX, evt.clientY, rowObject,
                columnObject, childElement);

            if (columnObject.value && rowObject.value != -1) {
                var item = tree.contentView.getItemAtIndex(rowObject.value);
                var pls = item.getAttribute("value");
                ajaxdj_ref.send_post_command('panelSet',
                    {type: "playlist", value:pls});
                }
            return true;
        },
    removePlaylist: function(value)
        {
            var rs = window.confirm(ajaxdj_ref.getString("confirm"));
            if (rs) {
                var list = new Array(value);
                ajaxdj_ref.send_post_command('playlistErase', {pl_ids: list});
                }
        },
};


function panelSelectObserver(evt) {
    var target_id = evt.target.id;
    var tag = target_id.replace("-panel", "");
    panel_ref.updatePanelFilter(tag);
};


// try to update panel in another thread do not work for now
/*
 * function to update panel in another thread
 */
/*var panelBuild = function(main, obj)
{
    this.obj = obj;
    this.main = main;

    this.run = function() {
        var list = this.obj.getElementsByTagName("item");
        var tag = this.obj.getAttribute("tag");
        this.main.dispatch(new panelUpdateUI(tag, list),
                this.main.DISPATCH_NORMAL);
    };

    this.QueryInterface = function(iid) {
        if (iid.equals(Components.interfaces.nsIRunnable) ||
            iid.equals(Components.interfaces.nsISupports)) {
                return this;
        }
        throw Components.results.NS_ERROR_NO_INTERFACE;
    }
};

var panelUpdateUI = function(obj)
{
    this.tag = tag;
    this.list = list;

    this.run = function() {
        var pn = $(this.tag+"-panel");
        // remove listener
        try { pn.removeEventListener("select", panelSelectObserver, false); }
        catch (ex) {}
        // remove old item
        while(pn.getRowCount() > 0) { pn.removeItemAt(0); }

        var idx = 0;
        for (var i=0; item = this.list[i]; i++) {
            var listitem = pn.appendItem(item.getAttribute("label"),
                    item.getAttribute("value"));
            if (item.getAttribute("selected") == "true") {
                var listitem = pn.getItemAtIndex(i);
                pn.addItemToSelection(listitem);
                if (idx == 0) { idx = i; }
                }
            }
        idx = Math.min(idx+1, pn.getRowCount()-1);
        pn.ensureIndexIsVisible(idx);

        // add listener
        pn.addEventListener("select", panelSelectObserver, false);
    };

    this.QueryInterface = function(iid) {
        if (iid.equals(Components.interfaces.nsIRunnable) ||
            iid.equals(Components.interfaces.nsISupports)) {
                return this;
        }
        throw Components.results.NS_ERROR_NO_INTERFACE;
    }
};*/

// vim: ts=4 sw=4 expandtab
