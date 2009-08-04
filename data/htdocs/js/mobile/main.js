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

var mobileui_ref;

function mobileUI()
{
    mobileui_ref = this;
    this.ref = 'mobileui_ref';

    this.init = function()
    {
        // build ui
        this.ui = new UI(this);

        this.rpc = new RPC(this, './../rpc/');
        this.rpc.callbacks = {
            updateMode: this.updateMode,
            updateOption: function(data) {
                mobileui_ref.updateMode(data);
                mobileui_ref.ui.getCurrentMode().closeExtra();
            },
            player: { def: this.updateStatus, },
            playlist: {
                def: this.updateMode,
                addPath: function(data) {
                    mobileui_ref.ui.displayMessage("Files has been loaded");
                    mobileui_ref.updateMode(null);
                },
            },
            video: { def: this.updateMode, },
            webradio: { def: this.updateMode, },
            panel: {
                def: this.updateMode,
                clearFilter: function(data) {},
                clearSearch: function(data) {},
            },
            dvd: this.updateMode,
        };
        this.rpc.onerror = function(request, error, exception){
            $("#fatal_error").html("Fatal Error " + error + " : "
                    + request.responseText).show();
        };
        this.rpc.onrequesterror = function(code, message){
            mobileui_ref.ui.displayMessage("Resquest Error " + code + " - "
                    + message, 'error');
        };

        this.updateStatus(null);
    }

/*
 * Callbacks
 */
    this.updateStatus = function(data)
    {
        var success = function(data) {
            mobileui_ref.ui.buildPage("now_playing", data);
        };
        mobileui_ref.rpc.send("status", [], success);
    };

    this.updateMode = function(data)
    {
        var success = function(data) {
            mobileui_ref.ui.buildPage("current_mode", data);
        };
        mobileui_ref.rpc.send("status", [], success);
    };

    this.updateVolume = function(orient)
    {
        var current = $('#volume-handle').attr("value");
        if (orient == "up") {
            var value = Math.min(parseInt(current) + 5, 100);
            }
        else if (orient == "down") {
            var value = Math.max(parseInt(current) - 5, 0);
            }
        mobileui_ref.rpc.setVolume(value);
    };

/*
 * localisation
 */
    this.getString = function(id, def)
    {
        var text = $("#i18n-"+id).html();
        if (!text)
            text = def;
        return text;
    };
}

$(document).ready( function() {
    var _mobileui = new mobileUI();
    _mobileui.init();
    setTimeout("window.scrollTo(0, 1);", 1000);
});

// vim: ts=4 sw=4 expandtab
