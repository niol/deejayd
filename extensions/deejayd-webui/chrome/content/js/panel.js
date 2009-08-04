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

function _LibPlsPanel(library, playlist) { return this; };
_LibPlsPanel.prototype =
{
    initialize: function(library, playlist) {
        this.__library = library;
        this.__playlist = playlist;

        var panel = this;
        if (this.__library) {
            this.__library.addListener(panel.onLibraryUpdate, panel);
        }
        if (this.__playlist) {
            this.__playlist.addListener(panel.onPlaylistUpdate, panel);
        }
    },

    onPlaylistUpdate: function(data, user_data) { },

    onLibraryUpdate: function(state, data, user_data) {
        var panel = user_data;
        switch (state) {
            case "start":
            $(panel.__button+"-update").selectedIndex = 1;
            $(panel.__button+'-update-progressbar').mode = "undetermined";
            break;

            case "finish":
            $(panel.__button+"-update").selectedIndex = 0;
            $(panel.__button+'-update-progressbar').mode = "determined";
            if (typeof(panel.rebuild) == "function")
                panel.rebuild();
            break;

            case "updated":
            if (typeof(panel.rebuild) == "function")
                panel.rebuild();
            break;
        }
    },

    __setLoading: function(list) {
        while (list.hasChildNodes())
            list.removeChild(list.firstChild);
        list.appendItem("Loading...");
    },
};

/*
 * for playlist mode
 */
function PlsModePanel(library, playlist) {
    this.__button = "audio";
    this.initialize(library, playlist);

    netscape.security.PrivilegeManager.
        enablePrivilege("UniversalXPConnect");
    var controller = {
        supportsCommand : function(cmd){ return (cmd == "cmd_selectAll"); },
        isCommandEnabled : function(cmd){return true; },
        doCommand : function(cmd) { slAll('file-content'); },
        onEvent : function(evt){ }
        };
    $('file-content').controllers.appendController(controller);

    return this;
};
PlsModePanel.prototype = new _LibPlsPanel;
PlsModePanel.prototype.__buildRow = function(type, data) {
    var row = document.createElement("listitem");
    row.setAttribute("type",type);
    for (key in data) { row.setAttribute(key, data[key]); }
    row.addEventListener('draggesture', function(evt) {
            var plainText = evt.target.getAttribute("type") + "-list";
            dragStart(evt, plainText);
        }, true);

    switch (type) {
        case "directory":
            row.className = "listitem-iconic directory-item";
            row.ondblclick = function(evt) {
                xului_ref.ui.panels.playlist.rebuild(evt.target.value);
            };
            break;
        case "audio-file":
            row.className = "audio-item listitem-iconic";
            break;
        case "playlist":
            row.className = data.pls_type+ "-playlist-item listitem-iconic";
            break;
    }
    return row;
};
PlsModePanel.prototype.constructMenu = function(path) {
    var navMenu = $("navigation-path");
    // erase previous menu
    while (navMenu.hasChildNodes())
        navMenu.removeChild(navMenu.firstChild);
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
        button.addEventListener('command', function(evt) {
                var path = evt.target.id == 'root_link' ? '': evt.target.id;
                xului_ref.ui.panels.playlist.rebuild(path);
            }, true);

        navMenu.appendChild(button);
        }
    navMenu.style.display="block";
};
PlsModePanel.prototype.rebuild = function(data) {
    var panel = this;
    var callback = function(data) {
        panel.constructMenu(data.root);

        var list = $('file-content');
        while (list.hasChildNodes())
            list.removeChild(list.firstChild);
        // build directories
        for (var i=0; dir=data.directories[i]; i++) {
            var path = data.root!="" ? data.root+"/"+dir : dir;
            var attrs = {label: dir, value: path, value_type: "path",
                context: "fileList-menu"};
            var row = panel.__buildRow("directory", attrs);
            list.appendChild(row);
        }
        // build files
        for (var i=0; f=data.files[i]; i++) {
            var path = data.root!="" ? data.root+"/"+f.filename : f.filename;
            var attrs = {label: f.filename, value: path, value_type: "path",
                context: "fileList-menu"};
            var row = panel.__buildRow("audio-file", attrs);
            list.appendChild(row);
        }
    };

    this.__setLoading($('file-content'));
    var parms = [];
    if (typeof(data) == "string") { parms.push(data); }
    xului_ref.rpc.send("audiolib.getDir", parms, callback);
};
PlsModePanel.prototype.getSelectedType = function(id) {
    var navList = $(id);
    var items = navList.selectedItems;
    try { var type = items[0].getAttribute("value_type"); }
    catch(ex) {
        var type = "path";
        }
    return type;
};
PlsModePanel.prototype.getSelectedItems = function(id) {
    var navList = $(id);
    var items = navList.selectedItems;
    var argArray = new Array();
    for (var id in items) {
        var item = items[id];
        argArray.push(item.value);
        }
    return argArray;
};
// Search part
PlsModePanel.prototype.searchFile = function() {
    var panel = this;
    var callback = function(data) {
        var list = $('file-content');
        while (list.hasChildNodes())
            list.removeChild(list.firstChild);
        for (var i=0; media=data.medias[i]; i++) {
            var attrs = {label: media.filename, value: media.media_id,
                value_type: "id", context: "fileList-menu"};
            var row = panel.__buildRow("audio-file", attrs);
            list.appendChild(row);
        }
    };

    var text = $('search-text').value;
    var typ = $('search-type').selectedItem.value;

    this.__setLoading($('file-content'));
    xului_ref.rpc.send("audiolib.search", [text, typ], callback);
};
PlsModePanel.prototype.searchClear = function() {
    $('search-text').value = "";
    this.rebuild();
};
// Recorded playlist part
PlsModePanel.prototype.onPlaylistUpdate = function(data, panel) {
    data = data.medias;
    var list = $('playlistList-content');
    while (list.hasChildNodes())
        list.removeChild(list.firstChild);
    for (var i=0; pls=data[i]; i++) {
        attrs = {pls_type: pls.type, label: pls.name, value: pls.id,
            context: "playlistList-menu"};
        var row = panel.__buildRow("playlist", attrs);
        list.appendChild(row);
    }

    // update playlist menu
    var menu = $('fileaddplaylist-menu');
    while (menu.hasChildNodes())
        menu.removeChild(menu.firstChild);

    for (var i=0; pls=data[i]; i++) {
        if (pls.type == "static") {
            var item = document.createElement("menuitem");
            item.setAttribute("label", pls.name);
            item.setAttribute("value", pls.id);
            item.addEventListener("command", function(evt) {
                    var pl_id = evt.target.value;
                    var selections = panel.getSelectedItems("file-content");
                    if (selections.length > 0) {
                        var type = panel.getSelectedType("file-content");
                        xului_ref.rpc.staticPlsAdd(pl_id, selections, type);
                    }
                }, true);
            menu.appendChild(item);
        }
    }
};
PlsModePanel.prototype.erasePlaylist = function() {
    var rs = window.confirm(xului_ref.getString("confirm"));
    if (rs)
        xului_ref.rpc.recPlsErase(
                this.getSelectedItems("playlistList-content"));
};

/*
 * for video mode
 */
function VideoModePanel(library) {
    this.__button = "video";
    this.tree = $("videodir-tree");
    this.initialize(library);
    return this;
};
VideoModePanel.prototype = new _LibPlsPanel;
VideoModePanel.prototype.rebuild = function(data) {
    var panel = this;
    var updateRDFSource = function(data) {
        if (!data.id)
            return true;
        // clear selection
        if (panel.tree.view)
            panel.tree.view.selection.clearSelection();

        netscape.security.PrivilegeManager.
            enablePrivilege("UniversalXPConnect");
        // Update datasources
        var RDF = Components.classes["@mozilla.org/rdf/rdf-service;1"].
            getService(Components.interfaces.nsIRDFService);
        var ds=RDF.GetDataSource(xului_ref.url+"tmp/videodir-"+data.id+".rdf");

        var currentSources = panel.tree.database.GetDataSources();
        while (currentSources.hasMoreElements()) {
            var src = currentSources.getNext();
            panel.tree.database.RemoveDataSource(src);
        }
        panel.tree.database.AddDataSource(ds);
        panel.tree.builder.rebuild();
    };

    xului_ref.rpc.send("web.buildSourceRDF", ["videodir"], updateRDFSource);
};
VideoModePanel.prototype.setDirectory = function(evt) {
    var childElement = {}, rowObject = {}, columnObject = {};
    this.tree.treeBoxObject.getCellAt(evt.clientX, evt.clientY, rowObject,
        columnObject, childElement);

    if (columnObject.value && rowObject.value != -1) {
        if (columnObject.value.index != 1)
            return true;
        var dir_item = this.tree.contentView.getItemAtIndex(rowObject.value);
        var dir = dir_item.id.replace("http://videodir/root/", "");
        xului_ref.rpc.videoSet(dir, "directory");
        }
    return true;
};
VideoModePanel.prototype.search = function() {
    var text = $('videosearch-text').value;
    if (text != "")
        xului_ref.rpc.videoSet(text, "search");
};

/*
 * for panel mode
 */
function PanelModePanel(library, rec_pls) {
    this.__button = "panel-audio";
    this.tree = $("panel-pls-list");
    this.initialize(library, rec_pls);

    // init drop event
    this.plsDropSupport = new TreeDropSupport(this.tree, function(pos, data) {
            if (pos == -1) { return; } // no playlist selected

            var pls = $('panel-pls-list').contentView.getItemAtIndex(pos);
            if (pls.getAttribute("pls-type") == 'magic' ||
                xului_ref.ui.modes.panel.selected_playlist
                        == pls.getAttribute("value"))
                return;

            if (data == 'panel')
                var sel = xului_ref.ui.modes.panel.getSelection("value");
            else if (data == 'queue')
                var sel = xului_ref.ui.queue.getSelection("value");
            xului_ref.rpc.staticPlsAdd(pls.getAttribute("value"), sel, "id");
        }, Array('panel', 'queue'));
    var user_agent = navigator.userAgent;
    if (user_agent.indexOf("rv:1.9.0") != -1) {
        this.tree.setAttribute("ondragdrop",
                "xului_ref.ui.panels.panel.plsDropSupport.drop(event);");
    }
    else if (user_agent.indexOf("rv:1.9.1") != -1) {
        this.tree.setAttribute("ondrop",
                "xului_ref.ui.panels.panel.plsDropSupport.drop(event);");
    }

    return this;
};
PanelModePanel.prototype = new _LibPlsPanel;
PanelModePanel.prototype.__clearMenu = function() {
    var menu = $("panel-pls-action-menu");
    while(menu.hasChildNodes())
        menu.removeChild(menu.firstChild);
};
PanelModePanel.prototype.__buildMenuItem = function(menu) {
    var obj = document.createElement("menuitem");
    obj.setAttribute("class", "menuitem-iconic " + menu.cls);
    obj.setAttribute("label", xului_ref.getString(menu.label));
    obj.setAttribute("oncommand", menu.command);

    $("panel-pls-action-menu").appendChild(obj);
};
PanelModePanel.prototype.updateMenu = function (evt) {
    // first remove old menuitem
    this.__clearMenu();
    var childElement = {}, rowObject = {}, columnObject = {};
    this.tree.treeBoxObject.getCellAt(evt.clientX, evt.clientY, rowObject,
        columnObject, childElement);

    if (columnObject.value && rowObject.value != -1) {
        var item = this.tree.contentView.getItemAtIndex(rowObject.value);
        if (item.getAttribute("pls-type") == "magic")
            this.__buildMenuItem({label: "edit", cls: "edit-action",
                command: "xului_ref.ui.panels.panel.editMagicPlaylist('"+
                item.getAttribute("value")+"');"});
        this.__buildMenuItem({label: "remove", cls: "remove-action",
            command: "xului_ref.ui.panels.panel.removePlaylist('"+
            item.getAttribute("value")+"');"});
    }
    else {
        this.__buildMenuItem({label: "newStaticPls",
            cls: "playlist-new",
            command: "xului_ref.ui.panels.panel.createStaticPlaylist();"});
        this.__buildMenuItem({label: "newMagicPls",
            cls: "playlist-new",
            command: "xului_ref.ui.panels.panel.createMagicPlaylist();"});
    }
};
PanelModePanel.prototype.removePlaylist = function(value) {
    var rs = window.confirm(xului_ref.getString("confirm"));
    if (rs)
        xului_ref.rpc.recPlsErase([value]);
};
PanelModePanel.prototype.__playlistPrompt = function(string1, string2) {
    var prompts =
        Components.classes["@mozilla.org/embedcomp/prompt-service;1"]
        .getService(Components.interfaces.nsIPromptService);
    var input = {value: ""};
    var check = {value: ""};
    var result = prompts.prompt(window,
            xului_ref.getString(string1),
            xului_ref.getString(string2), input, null, check);
    if (result && input.value != "") { return input.value; }
    return null;
};
PanelModePanel.prototype.createStaticPlaylist = function() {
    var pls_name = this.__playlistPrompt("newStaticPls", "enterPlsName");
    if (pls_name)
        xului_ref.rpc.recPlsCreate(pls_name, 'static');
};
PanelModePanel.prototype.__setMagicPlsAttr = function(pl_id, params) {
    var n_cb = function(data) {};
    xului_ref.rpc.send("recpls.magicClearFilter", [pl_id], n_cb);
    for (var i=0; filter=params.output.filters[i]; i++)
        xului_ref.rpc.send("recpls.magicAddFilter", [pl_id, filter], n_cb);
    for (var key in params.output.properties)
        xului_ref.rpc.send("recpls.magicSetProperty",
                [pl_id, key, params.output.properties[key]], n_cb);
};
PanelModePanel.prototype.createMagicPlaylist = function() {
    var pls_name = this.__playlistPrompt("newMagicPls", "enterPlsName");
    if (pls_name) {
        var params = {input: null, output: null,
            title: xului_ref.getFormattedString("magicPlsFilters",
                    [pls_name])};
        window.openDialog(
                'chrome://deejayd-webui/content/playlist-dialog.xul',
                'playlist-dialog', 'chrome, dialog, modal, resizable=yes',
                params).focus();
        if (params.output) {
            // create magic playlist
            var mode = this;
            var callback = function(data) {
                mode.__setMagicPlsAttr(data.pl_id, params);
                // update playlist list
                xului_ref.ui.rec_pls.update();
            };
            xului_ref.rpc.send("recpls.create", [pls_name, 'magic'], callback);
        }
    }
};
PanelModePanel.prototype.editMagicPlaylist = function(pl_id) {
    var mode = this;
    var f_callback = function(data) {
        var filters = data.filter.value;
        var p_callback = function(data) {
            var params = {input: {filters: filters, properties: data},
                output: null, title: null};
            window.openDialog(
                    'chrome://deejayd-webui/content/playlist-dialog.xul',
                    'playlist-dialog', 'chrome, dialog, modal, resizable=yes',
                    params).focus();
            if (params.output)
                mode.__setMagicPlsAttr(pl_id, params);
        };
        xului_ref.rpc.send("recpls.magicGetProperties", [pl_id], p_callback);
    };
    xului_ref.rpc.send("recpls.get", [pl_id], f_callback);
};
PanelModePanel.prototype.onPlaylistUpdate = function(data, panel) {
    var tree = $("panel-pls-list");
    var tree_children = $("panel-pls-list-children");
    // first Erase the playlist list
    while(tree_children.hasChildNodes())
        tree_children.removeChild(tree_children.firstChild);

    // insert new playlist
    var selected_index = -1;
    for (var i=0;playlist=data.medias[i];i++) {
        var plsItem = document.createElement("treeitem");
        plsItem.setAttribute("value", playlist.id);
        plsItem.setAttribute("pls-type", playlist.type);
        var plsRow = document.createElement("treerow");
        plsRow.setAttribute("value", playlist.id);
        plsRow.setAttribute("pls-type", playlist.type);

        var cell = document.createElement("treecell");
        cell.setAttribute("label", playlist.name);
        cell.setAttribute("properties", playlist.type+"-playlist-item");
        plsRow.appendChild(cell);

        plsItem.appendChild(plsRow);
        tree_children.appendChild(plsItem);

        if (playlist.id == xului_ref.ui.modes.panel.selected_playlist)
            selected_index = i;
    }
    // reselect current playlist
    if (selected_index != -1) {tree.view.selection.select(selected_index);}
};

// vim: ts=4 sw=4 expandtab
