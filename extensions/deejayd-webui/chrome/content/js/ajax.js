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


function httpRequest()
{
    this.url = '';
    this.busy = false;
    this.xmlhttp = null;

    this.reset = function()
    {
        // set unassigned event handlers
        this.onloading = function(){ };
        this.onloaded = function(){ };
        this.oninteractive = function(){ };
        this.oncomplete = function(){ };
        this.onabort = function(){ };
        this.onerror = function(){ };

        this.url = '';
        this.busy = false;
        this.xmlhttp = null;
    };

    this.build = function()
    {
        if (window.XMLHttpRequest)
            this.xmlhttp = new XMLHttpRequest();
        else if (window.ActiveXObject)
            this.xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
    };

    this.GET = function(url)
    {
        this.build();

        if (!this.xmlhttp) {
            this.onerror(this);
            return false;
        }

        var ref = this;
        this.url = url;
        this.busy = true;

        this.xmlhttp.onreadystatechange = function(){
                ref.xmlhttp_onreadystatechange(); };
        this.xmlhttp.open('GET', url);
        return this.xmlhttp.send(null);
    };

    this.POST = function(url, data, type)
    {
        this.build();

        if (!this.xmlhttp) {
            this.onerror(this);
            return false;
            }

        var ref = this;
        this.url = url;
        this.busy = true;

        this.xmlhttp.onreadystatechange = function(){
            ref.xmlhttp_onreadystatechange(); };
        this.xmlhttp.open('POST', url);
        this.xmlhttp.setRequestHeader('Content-Type', type);

        return this.xmlhttp.send(data);
    };

    this.xmlhttp_onreadystatechange = function()
    {
        if(this.xmlhttp.readyState == 1)
            this.onloading(this);

        else if(this.xmlhttp.readyState == 2)
            this.onloaded(this);

        else if(this.xmlhttp.readyState == 3)
            this.oninteractive(this);

        else if(this.xmlhttp.readyState == 4) {
            this.responseText = this.xmlhttp.responseText;
            this.responseXML = this.xmlhttp.responseXML;

            if(this.xmlhttp.status == 0)
                this.onabort(this);
            else if(this.xmlhttp.status == 200)
                this.oncomplete(this);
            else
                this.onerror(this);

            this.busy = false;
            }
    };

    // a best way to take http header
    this.get_header = function(name)
    {
        return this.xmlhttp.getResponseHeader(name);
    };

    this.reset();
}

// vim: ts=4 sw=4 expandtab
