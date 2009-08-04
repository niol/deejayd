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

function RecordedPlaylist()
{
    this.__listeners = [];
    this.list = [];
    return this;
};
RecordedPlaylist.prototype =
{
    update: function() {
        var rec_pls = this;
        var callback = function(data) {
            rec_pls.list = data.medias;
            for (var idx in rec_pls.__listeners) {
                rec_pls.__listeners[idx].func(data,
                        rec_pls.__listeners[idx].data);
            }
        };

        xului_ref.rpc.send("recpls.list", [], callback);
    },

    addListener: function(func, user_data) {
        this.__listeners.push({func: func, data: user_data});
    },
};

// vim: ts=4 sw=4 expandtab
