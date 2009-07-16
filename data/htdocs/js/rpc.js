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


function dump(arr,level) {
    var dumped_text = "";
    if(!level) level = 0;

    //The padding given at the beginning of the line.
    var level_padding = "";
    for(var j=0;j<level+1;j++) level_padding += "    ";

    if(typeof(arr) == 'object') { //Array/Hashes/Objects
        for(var item in arr) {
            var value = arr[item];

            if(typeof(value) == 'object') { //If it is an array,
                dumped_text += level_padding + "'" + item + "' ...\n";
                dumped_text += dump(value,level+1);
            } else {
                dumped_text += level_padding + "'" + item + "' => \"" + value + "\"\n";
            }
        }
    } else { //Stings/Chars/Numbers etc.
        dumped_text = "===>"+arr+"<===("+typeof(arr)+")";
    }
    return dumped_text;
}

function RPC(controller, url)
{
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
    },

    send: function(method, params, success) {
         var remote = this;
        // build data
        this._id += 1;
        var data = {method: method, params: params, id: this._id};
        // build success callback
        var callback = function(data) {
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
        $.ajax( {
            url: this._root,
            type: 'POST',
            contentType: 'json',
            dataType: 'json',
            cache: false,
            data: $.toJSON(data),
            error: function(request, error_string, exception){
                remote.onerror(request, error_string, exception, this) },
            success: callback
        } );
    },

/*
 * general requests
 */
    setMode: function(mode) {
        var controller = this._controller;
        this.send("setmode", [mode], controller.updateMode);
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
    plsModeAddPath: function(paths) {
       this.__plsModeRequest("addPath", [paths]);
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
 * Webradio requests
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

    pnModeClearFilter: function() { this.__pnModeRequest("clearFilter"); },
    pnModeClearSearch: function() { this.__pnModeRequest("clearSearch"); },
};

// vim: ts=4 sw=4 expandtab
