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

function Pager(func)
{
    this.NUMBER_PER_PAGE = 20;
    this.func = func;
    this.current_page = null;
    this.desc = null;

    return this;
}

Pager.prototype.build = function() {

    var pager = createElement("div", "pager", {});
    var first = createElement("div", "pager-first pager-btn", {});
    $(first).click(function(evt) {
        var mode = mobileui_ref.ui.getCurrentMode();
        var pager = mode.extra_pager;
        if (pager.current_page != 1)
            pager.func(evt, 1);
    });
    var previous = createElement("div", "pager-previous pager-btn", {});
    $(previous).click(function(evt) {
        var mode = mobileui_ref.ui.getCurrentMode();
        var pager = mode.extra_pager;
        if (pager.current_page > 1)
            pager.func(evt, pager.current_page - 1);
    });
    var next = createElement("div", "pager-next pager-btn", {});
    $(next).click(function(evt) {
        var mode = mobileui_ref.ui.getCurrentMode();
        var pager = mode.extra_pager;
        if (pager.current_page < pager.total_page)
            pager.func(evt, pager.current_page + 1);
    });
    var last = createElement("div", "pager-last pager-btn", {});
    $(last).click(function(evt) {
        var mode = mobileui_ref.ui.getCurrentMode();
        var pager = mode.extra_pager;
        if (pager.current_page != pager.total_page)
            pager.func(evt, pager.total_page);
    });

    var desc = createElement("div", "extra-pager-desc", {});
    $(desc).html(this.desc);
    $(pager).append(first).append(previous).append(desc).append(next).
             append(last);
    return pager;
};

Pager.prototype.update = function(length, current_page) {
    this.total_page = parseInt(parseInt(length)/this.NUMBER_PER_PAGE) + 1;
    this.current_page = current_page;
    this.desc = current_page+"/"+this.total_page;
};

Pager.prototype.registerFunction = function(func) {
    this.func = func;
};

// vim: ts=4 sw=4 expandtab
