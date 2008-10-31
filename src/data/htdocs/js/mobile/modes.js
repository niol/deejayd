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
           mobileui_ref.send_post_command(this.sourceName+"Remove",
                   {ids: this.get_selection()});
           }
   };

   this.clear = function()
   {
       mobileui_ref.send_command(this.sourceName+"Clear", {}, true);
   };

   this.set_option = function()
   {
        if (!this.has_playmode) { return false; }

        // update playorder option
        var val = $("#playorder-option").val();
        mobileui_ref.send_post_command("playorder",
                {source: this.sourceName, value: val}, true);
        // update repeat option
        val = $("#repeat-option")[0].checked ? "1" : "0";
        mobileui_ref.send_command("repeat",
                {source: this.sourceName, value: val}, true);
        // close extra page
        $('#mode-main').show();
        $('#mode-extra').hide();
   };
};

/************************************************************************/
/************************************************************************/
var PlaylistMode = function()
{
    this.sourceName = "playlist";
    this.has_selection = true;

    this.load_files = function()
    {
        var items = $(".library-select");
        var paths = new Array();
        for (var i = 0; item = items[i]; i++) {
            var input = item.getElementsByTagName("input").item(0);
            if (input && input.checked)
                paths.push(input.value)
            }
        mobileui_ref.send_post_command("playlistAdd", {values: paths}, true);

        // unchecked paths
        for (var i = 0; item = items[i]; i++) {
            var input = item.getElementsByTagName("input").item(0);
            if (input && input.checked)
                input.checked = false;
            }
    };

   this.shuffle = function()
   {
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
