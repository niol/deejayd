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

var Mode = function()
{
    this.has_playmode = true;
    this.has_selection = false;

    this.update_playmode = function(evt)
    {
        if (this.has_playmode) {
            mobileui_ref.send_post_command("playorder", {}, true);
            }
    };

    this.get_selection = function()
    {
        if (!this.has_selection) { return false; }

        var items = $(".media-select");
        var selections = new Array();
        for (var i = 0; item = items[i]; i++) {
            var input = item.getElementsByTagName("input").item(0);
            if (input.checked)
                selections.push(input.value)
            }
        return selections;
    };

   this.remove = function()
   {
       if (this.has_selection) {
           this.set_loading();
           mobileui_ref.send_post_command(this.sourceName+"Remove",
                   {ids: this.get_selection()});
           }
   };

   this.clear = function()
   {
       this.set_loading();
       mobileui_ref.send_command(this.sourceName+"Clear", {}, true);
   };

   this.set_loading = function()
   {
        $("#mode-content").hide();
        $("#mode-loading").show();
   };
};

/************************************************************************/
/************************************************************************/
var PlaylistMode = function()
{
    this.sourceName = "playlist";
    this.has_selection = true;

    this.__getLibrarySelection = function()
    {
        return;
    };

    this.add = function()
    {
        return;
    };

   this.shuffle = function()
   {
       this.set_loading();
       mobileui_ref.send_command("playlistShuffle", {}, true);
   };

};
// heritage by prototype
PlaylistMode.prototype = new Mode;

var playlist_ref = new PlaylistMode();

/************************************************************************/
/************************************************************************/

var PanelMode = function()
{
    this.sourceName = "panel";
};
// heritage by prototype
PanelMode.prototype = new Mode;

var panel_ref = new PanelMode();

/************************************************************************/
/************************************************************************/

var WebradioMode = function()
{
    this.sourceName = "webradio";
    this.has_selection = true;

    this.add = function()
    {
        return;
    };
};
// heritage by prototype
WebradioMode.prototype = new Mode;

var wb_ref = new WebradioMode();

// vim: ts=4 sw=4 expandtab
