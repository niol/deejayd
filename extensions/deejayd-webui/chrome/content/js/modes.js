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

function _Mode()
{
    this.__id = -1;
    this.__playing = null;
    this.__options = {playorder: null, repeat: null};
    this.__has_playorder = true;
    this.__has_repeat = true;
    this.__has_sort = false;
    // drag and drop support
    this.dropSupport = null;
};
_Mode.prototype =
{
    update: function(st) {
        // medialist update
        if (parseInt(st[this._mode]) != this.__id) {
            if (typeof this.__preUpdate == "function")
                this.__preUpdate(st);
            this.__id = parseInt(st[this._mode]);
            this.updateMedialist();
        }

        // playorder update
        if (this.__has_playorder &&
                this.__options.playorder!=st[this._mode+"playorder"]) {
            $(this._mode+"-playorder").value = st[this._mode+"playorder"];
            this.__options.playorder = st[this._mode+"playorder"];
        }

        // repeat update
        if (this.__has_repeat &&
                this.__options.repeat!=st[this._mode+"repeat"]) {
            $(this._mode+"-repeat").checked = st[this._mode+"repeat"]== "1" ?
                true : false;
            this.__options.repeat = st[this._mode+"repeat"];
        }
    },

    updateMedialist: function() {
        var mode = this;
        var updateRDFSource = function(data) {
            // first scroll to top
            var boxobject = mode.tree.treeBoxObject;
            boxobject.ensureRowIsVisible(0);

            // first reset sort
            if (mode.__has_sort)
                mode.resetSort();

            if (typeof mode.__preMedialistUpdate == "function")
                mode.__preMedialistUpdate(data);

            netscape.security.PrivilegeManager.
                enablePrivilege("UniversalXPConnect");
            // Update datasources
            var RDF = Components.classes["@mozilla.org/rdf/rdf-service;1"].
                getService(Components.interfaces.nsIRDFService);
            var ds = RDF.GetDataSource(xului_ref.url+"tmp/"+
                    mode._mode+"-"+mode.__id+".rdf");

            var currentSources = mode.tree.database.GetDataSources();
            while (currentSources.hasMoreElements()) {
                var src = currentSources.getNext();
                mode.tree.database.RemoveDataSource(src);
            }
            mode.tree.database.AddDataSource(ds);
            mode.tree.builder.rebuild();

            // set new sort
            if (mode.__has_sort && data.sort) {
                for (var i=0; sort = data.sort[i]; i++) {
                    var col = $(mode._mode+"-"+sort[0]);
                    col.setAttribute("sortActive", "true");
                    col.setAttribute("sortDirection", sort[1]);
                }
            }

            // update playing
            if (mode.playing != null) {
                mode.setPlaying(mode.__playing["pos"], mode.__playing["id"],
                        mode.__playing["state"]);
            }

            // update description
            $(mode._mode+"-description").value = data.desc;
        };

        xului_ref.rpc.send("web.buildSourceRDF", [mode._mode], updateRDFSource);
    },

    getSelection: function(type) {
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
    },

    /**************************************************************/
    // Event handler
    /**************************************************************/
    goToCurSong: function() {
        if (this.__playing != null) {
            var boxobject = this.tree.treeBoxObject;
            boxobject.ensureRowIsVisible(this.__playing["pos"]);
        }
    },

    play: function() {
        if (this.tree.contentView) {
            var item = this.tree.contentView.getItemAtIndex(
                            this.tree.currentIndex);
            var str = item.id;
            xului_ref.rpc.goto(str.split("/")[3]);
            }
    },

    showPopupMenu: function(evt) {
        var menu = $(this._mode+'-menu');
        menu.hidePopup();

        var childElement = {}, rowObject = {}, columnObject = {};
        this.tree.treeBoxObject.getCellAt(evt.clientX, evt.clientY, rowObject,
            columnObject, childElement);
        if (rowObject.value == -1)
            return;

        var context_x = evt.clientX + 5;
        var context_y = evt.clientY;
        menu.openPopup(null , "",context_x,context_y,true,false);
    },

    setPlayorder: function() {
        if (this.__has_playorder) {
            var val = $(this._mode + '-playorder').value;
            xului_ref.rpc.setOption(this._mode, "playorder", val);
        }
    },

    setRepeat: function() {
        if (this.__has_repeat) {
            var val = $(this._mode + '-repeat').checked;
            xului_ref.rpc.setOption(this._mode, "repeat", val);
        }
    },

    resetSort: function() {
        var cols = this.tree.getElementsByTagName("treecol");
        for (var i=0; col = cols.item(i); i++) {
            col.setAttribute("sortActive", "false");
            col.setAttribute("sortDirection", "");
            // workaround to force to update column state
            col.blur();
            col.focus();
            col.blur();
        }
    },

    // *****************************************************************
    // *****************************************************************
    setPlaying: function(pos, id, state) {
        try { var item = this.tree.contentView.getItemAtIndex(parseInt(pos)) }
        catch (ex) { // tree not ready
            var cmd = "xului_ref.ui.modes['"+this._mode+
                "'].setPlaying("+pos+","+id+",'"+state+"')";
            setTimeout(cmd,300);
            return;
            }

        if (item) {
            // get id of item
            var item_id = item.id;
            item_id = item_id.split("/")[3];
            if (item_id != id) // not the right row
                return;

            this.__playing = {"pos": pos, "id": id, "state": state};
            this.__playing["row"] = item.firstChild;
            this.__playing["row"].setAttribute("properties", state);
            this.__playing["cell"] = this.__playing["row"].firstChild;
            this.__playing["cell"].setAttribute("properties", state);
            }
    },

    updatePlaying: function(state) {
        if (this.__playing) {
            this.__playing['cell'].setAttribute("properties", state);
            this.__playing['row'].setAttribute("properties", state);
            this.__playing["state"] = state;
        }
    },

    resetPlaying: function() {
        if (this.__playing) {
            this.__playing["cell"].setAttribute("properties", "");
            this.__playing["row"].setAttribute("properties", "");
            this.__playing = null;
        }
    },

    /**************************************************************/
    // drag and drop support
    /**************************************************************/
    dragOver: function(evt) {
        if (this.dropSupport) { this.dropSupport.dragOver(evt); }
    },

    dragEnter: function(evt) {
        if (this.dropSupport) { this.dropSupport.dragEnter(evt); }
    },

    dragExit: function(evt) {
        if (this.dropSupport) { this.dropSupport.dragExit(evt); }
    },

    drop: function(evt) {
        evt.preventDefault();
        if (this.dropSupport) { this.dropSupport.drop(evt); }
    },
};

/*
 * Playlist Mode
 */
function PlaylistMode(lib_panel, rec_pls) {
    this._mode = "playlist";
    this.__lib_panel = lib_panel;
    this.tree = $("playlist-tree");
    $("playlist-source").hidden = false;

    // add recorded playlist listener
    rec_pls.addListener(function(data, panel) {
            data = data.medias;
            var menu = $("playlist-save-plslist");
            while(menu.hasChildNodes())
                menu.removeChild(menu.firstChild);

            for (var i=0;pls=data[i];i++) {
                if (pls.type == 'static') {
                    var item = document.createElement("menuitem");
                    item.setAttribute("label",pls.name);
                    menu.appendChild(item);
                }
            }
            // update playlist menu
            var menu = $('playlist-pls-menu');
            while (menu.hasChildNodes())
                menu.removeChild(menu.firstChild);

            for (var i=0; pls=data[i]; i++) {
                if (pls.type == "static") {
                    var item = document.createElement("menuitem");
                    item.setAttribute("label", pls.name);
                    item.setAttribute("value", pls.id);
                    item.addEventListener("command", function(evt) {
                        var pl_id = evt.target.value;
                        var selections = xului_ref.ui.modes.playlist.
                            getSelection("value");
                        if (selections.length > 0) {
                            xului_ref.rpc.staticPlsAdd(pl_id, selections, "id");
                        }
                    }, true);
                    menu.appendChild(item);
                }
            }
        }, this);

    // drag and drop support
    this.dropSupport = new TreeDropSupport(this.tree, function(pos, data) {
            if (data == 'playlist') {
                // move song at the new position
                var ids = xului_ref.ui.modes.playlist.getSelection("id");
                xului_ref.rpc.plsModeMove(ids, pos);
            }
            else if ((data == 'directory-list')||(data == 'audio-file-list'))
                xului_ref.ui.modes.playlist.loadFiles(pos);
            else if (data == 'playlist-list')
                xului_ref.ui.modes.playlist.loadPlaylist(pos);
      }, Array('playlist','playlist-list','directory-list','audio-file-list'));
    // add drop event listener
    // Specific for firefox 3.5
    var user_agent = navigator.userAgent;
    if (user_agent.indexOf("rv:1.9.0") != -1) {
        this.tree.setAttribute("ondragdrop",
                "xului_ref.ui.modes.playlist.drop(event);");
    }
    else if (user_agent.indexOf("rv:1.9.1") != -1) {
        this.tree.setAttribute("ondrop",
                "xului_ref.ui.modes.playlist.drop(event);");
    }
    return this;
};
PlaylistMode.prototype = new _Mode;
PlaylistMode.prototype.__preUpdate = function(st) {
    $("playlist-savebtn").disabled = st.playlistlength == "0";
};
PlaylistMode.prototype.togglePlaylistForm = function(print) {
    var plsForm = $('playlist-save-form');
    if (print == 1) {
        plsForm.style.display = "block";
        $('playlist-save-btn').selectedIndex = 1;
        $('playlist-save-list').focus();
    }
    else if (print == 0) {
        plsForm.style.display = "none";
        $('playlist-save-btn').selectedIndex = 0;
        $('playlist-save-list').value = "";
    }
};
PlaylistMode.prototype.savePlaylist = function() {
    var enable = true;
    var pls_name = $('playlist-save-list').value;

    var pls_list = xului_ref.ui.rec_pls.list;
    for (idx in pls_list) {
        if (pls_name == pls_list[idx].name) {
            enable = window.confirm(xului_ref.getString("replacePls"));
            break;
        }
    }

    if (enable) {
        xului_ref.rpc.plsModeSave(pls_name);
        this.togglePlaylistForm(0);
    }
};
PlaylistMode.prototype.loadFiles = function(pos) {
    var selections = this.__lib_panel.getSelectedItems("file-content");
    if (selections.length > 0) {
        var type = this.__lib_panel.getSelectedType("file-content");
        if (type == "path")
            xului_ref.rpc.plsModeAddPath(selections, pos);
        else if (type == "id")
            xului_ref.rpc.plsModeAddIds(selections, pos);
    }
};
PlaylistMode.prototype.loadPlaylist = function(pos) {
    var selections = this.__lib_panel.getSelectedItems("playlistList-content");
    if (selections.length > 0) {
        xului_ref.rpc.plsModeLoads(selections, pos);
    }
};
PlaylistMode.prototype.removeItems = function() {
    var ids = this.getSelection("id");
    xului_ref.rpc.plsModeRemove(ids);
};


/*
 * Video Mode
 */
function VideoMode(lib_panel) {
    this._mode = "video";
    this.__lib_panel = lib_panel;
    this.__has_sort = true;
    this.__selected_idx = {};
    this.tree = $("video-tree");
    $("video-source").hidden = false;
}
VideoMode.prototype = new _Mode;
VideoMode.prototype.updateSort = function(tag) {
    var pn_col = $('video-'+tag);
    var sort = [[tag, "ascending"]];
    if (pn_col.getAttribute("sortActive") == "true"
            && pn_col.getAttribute("sortDirection") == "ascending")
        sort = [[tag, "descending"]];
    else if (pn_col.getAttribute("sortActive") == "true"
            && pn_col.getAttribute("sortDirection") == "descending")
        sort = [];
    xului_ref.rpc.videoModeSetSort(sort);
};

/*
 * Webradio Mode
 */
function WebradioMode() {
    this._mode = "webradio";
    this.__has_playorder = false;
    this.__has_repeat = false;
    this.__selected_idx = {};
    this.tree = $("webradio-tree");
    $("webradio-source").hidden = false;
}
WebradioMode.prototype = new _Mode;
WebradioMode.prototype.add = function() {
    var nameParm = $('webradio-name').value;
    var urlParm = $('webradio-url').value;

    if (!nameParm || !urlParm) {
        alert(xului_ref.getString('missParm'));
        return;
        }
    xului_ref.rpc.wbModeAdd(nameParm, urlParm);

    // Clear form
    $('webradio-name').value = "";
    $('webradio-url').value = "";
};
WebradioMode.prototype.remove = function() {
    var ids = this.getSelection("id");
    xului_ref.rpc.wbModeRemove(ids);
};

/*
 * Panel Mode
 */
function PanelMode(rec_pls) {
    this._mode = "panel";
    this.__has_sort = true;
    this.__last_selected_tag = null;
    this.selected_playlist = null;
    this.selected_mode = null;
    this.selected_idx = {};
    this.tree = $("panel-tree");
    $("panel-source").hidden = false;
    // get tag list
    var panel = this;
    var callback = function(data) {
        for (var idx in data) {
            $(data[idx] + "-panel").hidden = false;
        }
        panel._tag_list = data;
    };
    xului_ref.rpc.send("panel.tags", [], callback);

    // add recorded playlist listener
    rec_pls.addListener(function(data, panel) {
            data = data.medias;
            var menu = $('panel-pls-menu');
            while (menu.hasChildNodes())
                menu.removeChild(menu.firstChild);

            for (var i=0; pls=data[i]; i++) {
                if (pls.type == "static") {
                    var item = document.createElement("menuitem");
                    item.setAttribute("label", pls.name);
                    item.setAttribute("value", pls.id);
                    item.addEventListener("command", function(evt) {
                        var pl_id = evt.target.value;
                        var sel=xului_ref.ui.modes.panel.getSelection("value");
                        if (sel.length > 0) {
                            xului_ref.rpc.staticPlsAdd(pl_id, sel, "id");
                        }
                    }, true);
                    menu.appendChild(item);
                }
            }
        }, this);

    return this;
};
PanelMode.prototype = new _Mode;
PanelMode.prototype.__preUpdate = function(st) {
    var mode = this;
    var callback = function(data) {
        var pls_tree = $('panel-pls-list');
        pls_tree.view.selection.clearSelection();
        if (data.type == "playlist") {
            mode.__setPanel(false);
            // select current playlist
            var items = pls_tree.getElementsByTagName("treerow");
            for (var i=0; item=items[i]; i++) {
                if (item.getAttribute("value") == data.value) {
                    pls_tree.view.selection.select(i);
                    break;
                }
            }
            mode.selected_playlist = data.value;
        }
        else if (data.type == "panel") {
            mode.__setPanel(true);
            var p_callback = function(data) {
                // update search bar
                if (data.search) {
                    var filter = data.search;
                    if (filter.type == "basic") {
                        $('panel-filter-text').value = filter.value.pattern;
                        $('panel-filter-type').value = filter.value.tag;
                    }
                    else if (filter.type == "complex") {
                        filter = filter.value[0];
                        $('panel-filter-text').value = filter.value.pattern;
                        $('panel-filter-type').value = "all";
                    }
                }
                else {
                    $('panel-filter-text').value= ""
                }
                // update panels
                for (var tag in data.panels) {
                    var pn = $(tag+"-panel");
                    // remove listener
                    try { pn.removeEventListener("select",
                            mode.panelSelectObserver, false); }
                    catch (ex) {}
                    // remove old item
                    pn.clearSelection();
                    while(pn.getRowCount() > 0) { pn.removeItemAt(0); }

                    mode.selected_idx[tag] = new Array();
                    for (var i=0; item = data.panels[tag][i]; i++) {
                        var listitem = pn.appendItem(item.name, item.value);
                        if (item.sel == "true")
                            mode.selected_idx[tag].push(i);
                    }
                    setTimeout("xului_ref.ui.modes.panel.setPanelSelection('"+
                            tag+"');",100);
                }
            };
            var parms = [];
            if (mode.__last_selected_tag)
                parms.push(mode.__last_selected_tag);
            xului_ref.rpc.send("web.buildPanel", parms, p_callback);
            mode.__last_selected_tag = null;
        }
    };
    xului_ref.rpc.send("panel.activeList", [], callback);
};
PanelMode.prototype.__setPanel = function(panel) {
    $('panel-select-button').checked = panel;
    $('filter-box').hidden = !panel;
    $('panel-box').hidden = !panel;
    this.selected_playlist = null;
    this.selected_mode = panel ? "panel" : "panel-playlist";
};
PanelMode.prototype.setPanelSelection = function(tag) {
    var pn = $(tag+"-panel");
    for (j in this.selected_idx[tag]) {
        pn.ensureIndexIsVisible(this.selected_idx[tag][j]);
        var listitem = pn.getItemAtIndex(this.selected_idx[tag][j]);
        pn.addItemToSelection(listitem);
    }

    // add listener
    pn.addEventListener("select", this.panelSelectObserver, false);
};
PanelMode.prototype.setPlaylist = function (evt) {
    var tree = $("panel-pls-list");
    var childElement = {}, rowObject = {}, columnObject = {};
    tree.treeBoxObject.getCellAt(evt.clientX, evt.clientY, rowObject,
        columnObject, childElement);

    if (columnObject.value && rowObject.value != -1) {
        var item = tree.contentView.getItemAtIndex(rowObject.value);
        var pls = item.getAttribute("value");
        xului_ref.rpc.pnModeSetActiveList("playlist", pls);
    }
    return true;
};
PanelMode.prototype.updatePanelFilterText = function() {
    var tag = $("panel-filter-type").value;
    var value = $("panel-filter-text").value;
    xului_ref.rpc.pnModeSetSearch(tag, value);
};
PanelMode.prototype.clearPanelFilterText = function() {
    $("panel-filter-text").value = "";
    xului_ref.rpc.pnModeClearSearch();
};
PanelMode.prototype.updateSort = function(tag) {
    var pn_col = $('panel-'+tag);
    var sort = [[tag, "ascending"]];
    if (pn_col.getAttribute("sortActive") == "true"
            && pn_col.getAttribute("sortDirection") == "ascending")
        sort = [[tag, "descending"]];
    else if (pn_col.getAttribute("sortActive") == "true"
            && pn_col.getAttribute("sortDirection") == "descending")
        sort = [];
    xului_ref.rpc.pnModeSetSort(sort);
};
// Observers
PanelMode.prototype.panelSelectObserver = function(evt) {
    var tag = evt.target.id.replace("-panel", "");
    var listbox = evt.target;
    var values = new Array();
    for (var i=0; item = listbox.getSelectedItem(i); i++) {
        if (item.getAttribute("value") == "__all__") {
            xului_ref.ui.modes.panel.__last_selected_tag = tag;
            xului_ref.rpc.pnModeRemoveFilter(tag);
            return;
        }
        values.push(item.getAttribute("value"))
    }
    xului_ref.ui.modes.panel.__last_selected_tag = tag;
    xului_ref.rpc.pnModeSetFilter(tag, values);
};

/*
 * dvd
 */
function DvdMode() {
    this._mode = "dvd";
    this.__has_playorder = false;
    this.__has_repeat = false;
    this.tree = $("dvd-tree");
    $("dvd-source").hidden = false;
};
DvdMode.prototype = new _Mode;
DvdMode.prototype.__preMedialistUpdate = function(data) {
    $("dvdinfo-title").value = data.title;
    //$("dvdinfo-longest_track").value = data.longest_track;
};
DvdMode.prototype.play = function() {
    if (this.tree.contentView) {
        var item = this.tree.contentView.getItemAtIndex(this.tree.currentIndex);
        var str = item.id;
        str = str.split("/")

        var id_value = str[3];
        if (str.length > 4)
            id_value += "."+str[4]

        xului_ref.rpc.goto(id_value, "dvd_id");
        }
    return false;
};

/*
 * Queue
 */
function Queue(rec_pls) {
    this._mode = "queue";
    this.__has_playorder = false;
    this.__has_repeat = false;
    this.tree = $("queue-tree");
    // drag and drop support
    this.dropSupport = new TreeDropSupport(this.tree, function(pos, data) {
            if (data == 'queue') {
                // move song at the new position
                var ids = xului_ref.ui.queue.getSelection("id");
                xului_ref.rpc.queueMove(ids, pos);
            }
            else if (data == "panel" || data == "panel-playlist") {
                var ids = xului_ref.ui.modes.panel.getSelection("value");
                xului_ref.rpc.queueAddIds(ids, pos);
            }
            else if ((data == 'directory-list')||(data == 'audio-file-list'))
                xului_ref.ui.queue.loadFiles(pos);
            else if (data == 'playlist-list')
                xului_ref.ui.queue.loadPlaylist(pos);
      }, Array('queue', 'panel',"panel-playlist", 'playlist-list',
               'directory-list','audio-file-list'));
    // add drop event listener
    // Specific for firefox 3.5
    var user_agent = navigator.userAgent;
    if (user_agent.indexOf("rv:1.9.0") != -1) {
        this.tree.setAttribute("ondragdrop", "xului_ref.ui.queue.drop(event);");
    }
    else if (user_agent.indexOf("rv:1.9.1") != -1) {
        this.tree.setAttribute("ondrop", "xului_ref.ui.queue.drop(event);");
    }

    // add recorded playlist listener
    rec_pls.addListener(function(data, panel) {
            data = data.medias;
            var menu = $('queue-pls-menu');
            while (menu.hasChildNodes())
                menu.removeChild(menu.firstChild);

            for (var i=0; pls=data[i]; i++) {
                if (pls.type == "static") {
                    var item = document.createElement("menuitem");
                    item.setAttribute("label", pls.name);
                    item.setAttribute("value", pls.id);
                    item.addEventListener("command", function(evt) {
                        var pl_id = evt.target.value;
                        var sel = xului_ref.ui.queue.getSelection("value");
                        if (sel.length > 0) {
                            xului_ref.rpc.staticPlsAdd(pl_id, sel, "id");
                        }
                    }, true);
                    menu.appendChild(item);
                }
            }
        }, this);

    return this;
};
Queue.prototype = new _Mode;
Queue.prototype.__preUpdate = function(st) {
    $('queue-playorder').checked = st.queueplayorder == "random" ? true : false;
};
Queue.prototype.toogleQueue = function() {
    var currentState = $('queue-splitter').getAttribute("state");
    if (currentState == "collapsed") {
        $('queue-splitter').setAttribute("state","open");
        $('queue-splitter').style.visibility = "visible";
        $('queue-button').className = "expanded";
        $('queue-actions').style.visibility = "visible";
        }
    else {
        $('queue-splitter').setAttribute("state","collapsed");
        $('queue-button').className = "collapsed";
        $('queue-actions').style.visibility = "hidden";
        $('queue-splitter').style.visibility = "collapse";
        }
};
Queue.prototype.play = function() {
    if (this.tree.contentView) {
        var item = this.tree.contentView.getItemAtIndex(this.tree.currentIndex);
        var str = item.id;
        xului_ref.rpc.goto(str.split("/")[3], "id", "queue");
    }
};
Queue.prototype.toggleRandom = function() {
    if ($('queue-playorder').checked)
        var state = "random";
    else
        var state = "inorder";
    xului_ref.rpc.setOption("queue", "playorder", state);
    return false;
};
Queue.prototype.loadFiles = function(pos) {
    var sel = xului_ref.ui.panels.playlist.getSelectedItems("file-content");
    if (sel.length > 0) {
        var type = xului_ref.ui.panels.playlist.getSelectedType("file-content");
        if (type == "path")
            xului_ref.rpc.queueAddPath(sel, pos);
        else if (type == "id")
            xului_ref.rpc.queueAddIds(sel, pos);
    }
};
Queue.prototype.loadPlaylist = function(pos) {
    var selections = xului_ref.ui.panels.playlist.
        getSelectedItems("playlistList-content");
    if (selections.length > 0) {
        xului_ref.rpc.queueLoads(selections, pos);
    }
};
Queue.prototype.loadFromPanel = function(pos) {
    var selections = xului_ref.ui.modes.panel.getSelection("value");
    if (selections.length > 0)
        xului_ref.rpc.queueAddIds(selections, pos);
};
Queue.prototype.removeItems = function() {
    var ids = this.getSelection("id");
    xului_ref.rpc.queueRemove(ids);
};


// vim: ts=4 sw=4 expandtab
