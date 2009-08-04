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


function buildJSONObject() {
    var Ci = Components.interfaces;
    var Cc = Components.classes;
    var nativeJSON = Cc["@mozilla.org/dom/json;1"].createInstance(Ci.nsIJSON);
    return {
        stringify: nativeJSON.encode,
        parse: nativeJSON.decode,
    }
}
if (typeof(JSON) != "object") {
    var JSON = buildJSONObject();
}

function RPC(controller, url)
{
    this.http_sockets = new Array();
    this.initialize(controller, url);
    return this;
}

RPC.prototype =
{
    initialize: function(controller, url) {
        this._controller = controller;
        this._root = url;
        this._id = 0;

        // init default callback
        this.callbacks = {};
        this.onerror = function(request, error_string, exception) {};
        this.onrequesterror = function(code, message) {};
        this.onrequeststart = function() {};
        this.onrequeststop = function() {};
    },

    __get_request_obj: function() {
        for (var n=0; n<this.http_sockets.length; n++) {
            if (!this.http_sockets[n].busy)
                return this.http_sockets[n];
            }

        var i = this.http_sockets.length;
        this.http_sockets[i] = new httpRequest();

        return this.http_sockets[i];
    },

    send: function(method, params, success) {
        var remote = this;
        var request_obj = this.__get_request_obj();

        if (request_obj) {
            remote.onrequeststart();

            // build data
            this._id += 1;
            var data = {method: method, params: params, id: this._id};
            // serialize data
            data = JSON.stringify(data);

            // build success callback
            request_obj.oncomplete = function(obj) {
                remote.onrequeststop();

                // parse json data
                data = JSON.parse(obj.responseText);
                if (data.error != null) { // request error
                    remote.onrequesterror(data.error.code, data.error.message);
                }
                else {
                    if (data.result && data.result.type)
                        success(data.result.answer);
                    else
                        success(data.result);
                }
            };
            // build error callback
            request_obj.onerror = function() {
                remote.onrequeststop();
                remote.onerror();
            };

            request_obj.POST(this._root, data, "json");
        }
    },

/*
 * general requests
 */
    setMode: function(mode) {
        this.send("setmode", [mode], this.callbacks.updateMode);
    },

    setOption: function(source, name, value) {
        this.send("setOption", [source, name, value],
                this.callbacks.updateOption);
    },

    setMediaRating: function(ids, value) {
        this.send("setRating", [ids, value], this.callbacks.updateRating);
    },

/*
 * player requests
 */
    __playerRequest: function(request, params) {
        var pl_callbacks = this.callbacks.player;
        if (pl_callbacks[request])
            var callback = pl_callbacks[request];
        else
            var callback = pl_callbacks.def;
        var p = params ? params : [];
        this.send("player."+request, p, callback);
    },

    playToggle: function() { this.__playerRequest("playToggle"); },
    stop: function() { this.__playerRequest("stop"); },
    next: function() { this.__playerRequest("next"); },
    previous: function() { this.__playerRequest("previous"); },
    goto: function(id, id_type, source) {
        var parms = [id];
        if (id_type) { parms.push(id_type); }
        if (source) { parms.push(source); }
        this.__playerRequest("goto", parms);
    },
    setVolume: function(vol) { this.__playerRequest("setVolume",[vol]); },
    seek: function(pos, rel) { this.__playerRequest("seek", [pos, rel]); },
    setPlayerOption: function(opt_name, opt_value) {
        this.__playerRequest("setPlayerOption",[opt_name, opt_value]);
    },

/*
 * playlist requests
 */
    __plsModeRequest: function(request, params) {
        var pl_callbacks = this.callbacks.playlist;
        if (pl_callbacks[request])
            var callback = pl_callbacks[request];
        else
            var callback = pl_callbacks.def;
        var p = params ? params : [];
        this.send("playlist."+request, p, callback);
    },

    plsModeShuffle: function() { this.__plsModeRequest("shuffle"); },
    plsModeClear: function() { this.__plsModeRequest("clear"); },
    plsModeRemove: function(ids) { this.__plsModeRequest("remove", [ids]); },
    plsModeMove: function(ids, pos) {
        this.__plsModeRequest("move", [ids, pos]);
    },
    plsModeAddPath: function(paths, pos) {
       var parms = [paths];
       if (typeof(pos) != "undefined" && pos != -1)
           parms.push(pos);
       this.__plsModeRequest("addPath", parms);
    },
    plsModeAddIds: function(ids, pos) {
       var parms = [ids];
       if (typeof(pos) != "undefined" && pos != -1)
           parms.push(pos);
       this.__plsModeRequest("addIds", parms);
    },
    plsModeLoads: function(pl_ids, pos) {
       var parms = [pl_ids];
       if (typeof(pos) != "undefined" && pos != -1)
           parms.push(pos);
       this.__plsModeRequest("loads", parms);
    },
    plsModeSave: function(pls_name) {
       this.__plsModeRequest("save", [pls_name]);
    },

/*
 * queue requests
 */
    __queueRequest: function(request, params) {
        var p = params ? params : [];
        this.send("queue."+request, p, this.callbacks.queue);
    },

    queueClear: function() { this.__queueRequest("clear"); },
    queueMove: function(ids, pos) { this.__queueRequest("move", [ids, pos]); },
    queueRemove: function(ids) { this.__queueRequest("remove",[ids]); },
    queueAddPath: function(paths, pos) {
       var parms = [paths];
       if (typeof(pos) != "undefined" && pos != -1)
           parms.push(pos);
       this.__queueRequest("addPath", parms);
    },
    queueAddIds: function(ids, pos) {
       var parms = [ids];
       if (typeof(pos) != "undefined" && pos != -1)
           parms.push(pos);
       this.__queueRequest("addIds", parms);
    },
    queueLoads: function(pl_ids, pos) {
       var parms = [pl_ids];
       if (typeof(pos) != "undefined" && pos != -1)
           parms.push(pos);
       this.__queueRequest("loads", parms);
    },

/*
 * video requests
 */
    __videoModeRequest: function(request, params) {
        var video_callbacks = this.callbacks.video;
        if (video_callbacks[request])
            var callback = video_callbacks[request];
        else
            var callback = video_callbacks.def;
        var p = params ? params : [];
        this.send("video."+request, p, callback);
    },

    videoSet: function(val, type) {
        this.__videoModeRequest("set",[val, type]);
    },
    videoModeSetSort: function(sort) {
        this.__videoModeRequest("sort",[sort]);
    },

/*
 * Webradio requests
 */
    __wbModeRequest: function(request, params) {
        var wb_callbacks = this.callbacks.webradio;
        if (wb_callbacks[request])
            var callback = wb_callbacks[request];
        else
            var callback = wb_callbacks.def;
        var p = params ? params : [];
        this.send("webradio."+request, p, callback);
    },

    wbModeClear: function() { this.__wbModeRequest("clear"); },
    wbModeRemove: function(val) { this.__wbModeRequest("remove",[val]); },
    wbModeAdd: function(name, url) { this.__wbModeRequest("add",[name, url]); },

/*
 * dvd requests
 */
    dvdReload: function() {
        this.send("dvd.reload", [], this.callbacks.dvd);
    },

/*
 * panel requests
 */
    __pnModeRequest: function(request, params) {
        var pn_callbacks = this.callbacks.panel;
        if (pn_callbacks[request])
            var callback = pn_callbacks[request];
        else
            var callback = pn_callbacks.def;
        var p = params ? params : [];
        this.send("panel."+request, p, callback);
    },

    pnModeSetActiveList: function(type, val) {
        this.__pnModeRequest("setActiveList",[type, val]);
    },
    pnModeClearAll: function() { this.__pnModeRequest("clearAll"); },
    pnModeClearFilter: function() { this.__pnModeRequest("clearFilter"); },
    pnModeClearSearch: function() { this.__pnModeRequest("clearSearch"); },
    pnModeSetSort: function(sort) { this.__pnModeRequest("setSort",[sort]); },
    pnModeSetSearch: function(tag, val) {
        this.__pnModeRequest("setSearch",[tag, val]);
    },
    pnModeSetFilter: function(tag, values) {
        this.__pnModeRequest("setFilter",[tag, values]);
    },

/*
 * recorded playlist requests
 */
    __recPlsRequest: function(request, params) {
        var p = params ? params : [];
        this.send("recpls."+request, p, this.callbacks.recpls);
    },

    staticPlsAdd: function(pl_id, values, type) {
        this.__recPlsRequest("staticAdd",[pl_id, values, type]);
    },
    recPlsErase: function(pl_ids) { this.__recPlsRequest("erase",[pl_ids]); },
    recPlsCreate: function(name, type) {
        this.__recPlsRequest("create",[name, type]);
    },
};

// vim: ts=4 sw=4 expandtab
