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

var UIController = function(mainController)
{
    this.current_msg = null;
    this.mainController = mainController;

    this.set_busy = function(a)
    {
        var state = a ? "block" : "none";
        $('#loading').style.display = state;
    };

    this.display_message = function(msg, type)
    {
        $("#notification").className = "";
        this.current_msg = msg;
    };

    this.hide_message = function()
    {
        if (this.current_msg != null) {
            $("#notification").className = "hide";
            this.current_msg = null;
            }
    };

    this.parseXMLAnswer = function(xmldoc)
    {
        rs = xmldoc.getElementsByTagName("block").item(0);
        if (rs) {
            for (var i=0; inner=rs.item(i); i++) {
                var content = inner.firstChild.data;
                $("#"+inner.getAttribute('name')).html(content);
                }
            }

        rs = xmldoc.getElementsByTagName("media_list").item(0);
        if (rs) {
            }

        rs = xmldoc.getElementsByTagName("player").item(0);
        if (rs) {
            }
    };

}

// vim: ts=4 sw=4 expandtab
