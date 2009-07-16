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

function formatTime(time)
{
    var sec = time % 60;
    if (sec < 10)
        sec = "0" + sec;
    var min = parseInt(time/60);
    if (min > 60) {
        var hour = parseInt(min/60);
        min = min % 60;
        if (min < 10)
            min = "0" + min;
        return hour + ":" + min + ":" + sec;
        }
    else {
        if (min < 10)
            min = "0" + min;
        return min + ":" + sec;
        }
}

function urlencode(str) {
  var output = new String(encodeURIComponent(str));
  output = output.replace(/'/g,"%27");
  return output;
}

function createElement(name, cls, attributes)
{
    var div = document.createElement(name);
    $(div).addClass(cls);
    for (attr in attributes)
        $(div).attr(attr, attributes[attr]);
    return div;
};

// vim: ts=4 sw=4 expandtab
