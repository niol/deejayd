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

function _Library()
{
    this.__last_updated = -1;
    this.__type = "unknown";
    this.__listeners = [];
    return this;
};
_Library.prototype =
{
    update: function(stats) {
        var last_update = parseInt(stats[this.__type+"_library_update"]);
        if (last_update != this.__last_updated) {
            this.__last_updated = last_update;
            for (var idx in this.__listeners) {
                this.__listeners[idx].func("updated", stats,
                        this.__listeners[idx].data);
            }
        }
    },

    addListener: function(func, user_data) {
        this.__listeners.push({func: func, data: user_data});
    },

    launchUpdate: function() {
        var type = this.__type;
        var callback = function(data) {
            var id = data[type+"_updating_db"];
            setTimeout("xului_ref.ui.libraries."+type+".verifyUpdate("+id+")",
                    1000);
        };
        xului_ref.rpc.send(this.__type+"lib.update", [], callback);
        for (var idx in this.__listeners) {
            this.__listeners[idx].func("start",null,this.__listeners[idx].data);
        }
    },

    verifyUpdate: function(id) {
        var library = this;
        var callback = function(data) {
            var type = library.__type;
            if (data[type+"_updating_db"] && data[type+"_updating_db"] == id)
                setTimeout("xului_ref.ui.libraries."+type+
                        ".verifyUpdate("+id+")", 1000);
            else if (data[type+"_updating_error"]) {
                // error in update process, report it
                xului_ref.displayMessage(data[type+"_updating_error"], 'error');
            }
            else {
                xului_ref.displayMessage(
                        xului_ref.getString(library.__type+"Update"));
                for (var idx in library.__listeners) {
                    library.__listeners[idx].func("finish", null,
                            library.__listeners[idx].data);
                }
            }
        };
        xului_ref.rpc.send("status", [], callback);
    },
};

function AudioLibrary()
{
    this.__type = "audio";
    return this;
};
AudioLibrary.prototype = new _Library;

function VideoLibrary()
{
    this.__type = "video";
    return this;
};
VideoLibrary.prototype = new _Library;

// vim: ts=4 sw=4 expandtab
