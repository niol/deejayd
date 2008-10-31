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

var mobileui_ref;

function buttonClick(evt) {
    mobileui_ref.send_command("setPage",
            {page: evt.target.getAttribute('value')}, true);
}

function mobileUI()
{
    this.message_time = 4000;
    mobileui_ref = this;
    this.ref = 'mobileui_ref';
    this.media_list = {source: ""};

    // handler on ajax event
    $("#loading").ajaxStart(function(){ $(this).show(); });
    $("#loading").ajaxStop(function(){ $(this).hide(); });

    this.init = function()
    {
        this.send_command('init',null,true);
    }

    this.display_message = function(msg, type)
    {
        var cont = msg;
        if (type == 'error')
            cont = '<input type="submit" onclick="mobileui_ref.hide_message();'+
                        ' return false;" value="Close"/>' + cont;
        cont = '<div class="'+type+'">'+cont+'</div>';

        $("#notification").html(cont).show();
        if (type != 'error') {
            setTimeout(this.ref+'.hide_message()', this.message_time);
            }
    };

    this.hide_message = function() { $("#notification").hide(); }

    this.format_ajax_parms = function(parm)
    {
        var toSend = '';
        if (typeof parm == 'object') {
            for (var i in parm) {
                if (typeof parm[i] == 'object') {
                    var obj = parm[i];
                    for (var j in obj)
                        toSend += (toSend?'&':'') + i + '=' + urlencode(obj[j]);
                    }
                else
                    toSend += (toSend? '&' : '') + i + '=' + urlencode(parm[i]);
                }
            }
        else
            toSend = parm;

        return toSend;
    };

    this.send_http_request = function(type, url, parm, lock)
    {
        var options = {
            "type": type,
            "url": url,
            "dataType": "xml",
            "success": mobileui_ref.parseXMLAnswer,
            "error": function(request,error) {
                $("#fatal_error").html("Erreur Fatale " + error + " : "
                    + request.responseText);
                }
            }
        if (type == "POST")
            options.data = this.format_ajax_parms(parm);
        $.ajax(options);
    };

    this.send_command = function(command, args, lock)
    {
        var cmd = command;
        if (typeof args == 'object') {
            for (var i in args)
                cmd += '&' + i + '=' + args[i];
            }
        this.send_http_request('GET',
            window.location.href+'commands?action='+cmd,'',lock);
        return false;
    }

    this.send_post_command = function(command,args)
    {
        this.send_http_request('POST',
            window.location.href+'commands?action='+command,args,true);
        return false;
    }

    this.updateVolume = function(orient)
    {
        var current = $('#volume-handle').attr("value");
        if (orient == "up") {
            var value = Math.min(parseInt(current) + 5, 100);
            }
        else if (orient == "down") {
            var value = Math.max(parseInt(current) - 5, 0);
            }
        mobileui_ref.send_command("setVol", {volume: value}, true);
    };

    this.parseXMLAnswer = function(xmldoc)
    {
        rs = xmldoc.getElementsByTagName("block");
        for (var i=0; inner=rs.item(i); i++) {
            var content = '';
            var parts_obj = inner.getElementsByTagName('part');
            for(var j=0; part=parts_obj.item(j); j++) {
                if (part.firstChild)
                    content += part.firstChild.data;
                }

            // Formatte le texte avant d'être insérer
            content = content.replace(/\'/g,"'");
            content = content.replace(/\"/g,'"');

            if (content != '') {
                $("#"+inner.getAttribute('name')).show().html(content);
                }
            else { $("#"+inner.getAttribute('name')).hide(); }
            }

        rs = xmldoc.getElementsByTagName("page_btn").item(0);
        if (rs) {
            var buttons = rs.getElementsByTagName("btn");
            for (var i=0; btn=buttons.item(i); i++) {
                if (btn.firstChild) {
                    var content = btn.firstChild.data;
                    $("#"+btn.getAttribute('name')).show().html(content);
                    $("#"+btn.getAttribute('name')).attr("value",
                            btn.getAttribute('link'));
                    $("#"+btn.getAttribute('name')).
                        unbind("click",buttonClick).click(buttonClick);
                    }
                else { $("#"+btn.getAttribute('name')).hide(); }
                }
            }

        rs = xmldoc.getElementsByTagName("medialist").item(0);
        if (rs) {
            // update medialist info
            mobileui_ref.media_list = {
                page: rs.getAttribute("page"),
                page_total: rs.getAttribute("page_total"),
                source: rs.getAttribute("source"),
                id: rs.getAttribute("id")
                };
            }

        rs = xmldoc.getElementsByTagName("player").item(0);
        if (rs) {
            // update state
            var state = rs.getElementsByTagName("state").item(0);
            if (state)
                $("#playpause_button").
                  attr("class", "control-button "+ state.getAttribute("value"));
            // update volume
            var volume = rs.getElementsByTagName("volume").item(0);
            var left = parseInt(volume.getAttribute("value"))*2 - 12;
            $("#volume-handle").attr("value", volume.getAttribute("value"));
            $("#volume-handle").css("left", left+"px");
            }

        rs = xmldoc.getElementsByTagName("extra_page").item(0);
        if (rs) {
            $("#mode-extra-title").html(rs.getAttribute("title"));

            $("#mode-main").hide();
            $("#mode-extra").show();
            }

        rs = xmldoc.getElementsByTagName("message").item(0);
        if (rs)
            mobileui_ref.display_message(rs.firstChild.data,
                rs.getAttribute("type"));

        window.scrollTo(0, 1);
    };

    /*
     * medialist pager
     */
    this.medialist_previous = function()
    {
        if (mobileui_ref.media_list.page > 1) {
            this.send_command("mediaList",
                    {page: parseInt(mobileui_ref.media_list.page)-1},true);
            }
    };

    this.medialist_next = function()
    {
        if (mobileui_ref.media_list.page<mobileui_ref.media_list.page_total) {
            this.send_command("mediaList",
                    {page: parseInt(mobileui_ref.media_list.page)+1},true);
            }
    };

    this.medialist_first = function()
    {
        if (mobileui_ref.media_list.page > 1) {
            this.send_command("mediaList",{page: 1},true);
            }
    };

    this.medialist_last = function()
    {
        if (this.media_list.page < this.media_list.page_total) {
            this.send_command("mediaList",
                    {page: this.media_list.page_total},true);
            }
    };
}

window.onload = function(e)
{
    var _mobileui = new mobileUI();
    _mobileui.init();
};

// vim: ts=4 sw=4 expandtab
