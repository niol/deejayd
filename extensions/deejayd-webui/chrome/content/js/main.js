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

/****************************************************************************/
/* Common functions
/****************************************************************************/
function $(id) {
  return document.getElementById(id);
}

function formatTime(time)
{
    var sec = parseInt(time % 60);
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

function Dump(arr,level) {
    var dumped_text = "";
    if(!level) level = 0;

    //The padding given at the beginning of the line.
    var level_padding = "";
    for(var j=0;j<level+1;j++) level_padding += "    ";

    if(typeof(arr) == 'object') { //Array/Hashes/Objects
        for(var item in arr) {
            var value = arr[item];

            if(typeof(value) == 'object') { //If it is an array,
                dumped_text += level_padding + "'" + item + "' ...\n";
                dumped_text += dump(value,level+1);
            } else {
                dumped_text += level_padding + "'" + item +
                    "' => \"" + value + "\"\n";
            }
        }
    } else { //Stings/Chars/Numbers etc.
        dumped_text = "===>"+arr+"<===("+typeof(arr)+")";
    }
    return dumped_text;
}

function urlencode(str) {
  var output = new String(encodeURIComponent(str));
  output = output.replace(/'/g,"%27");
  return output;
}

function eregReplace(search, replace, subject) {
	return subject.replace(new RegExp(search,'g'), replace);
}

function toogleNodeVisibility(node) {
    if (typeof node == 'string')
        node = $(node);

    var newState = node.style.visibility == "visible" ? "collapse" : "visible";
    node.style.visibility = newState;
}

function removeNode(node) {
    if (typeof node == 'string')
        node = $(node);

    if (node && node.parentNode)
        return node.parentNode.removeChild(node);
    else
        return false;
}

function replaceNodeText(node,content) {
    text = document.createTextNode(content);
    if (typeof node == 'string')
        node = $(node);

    if (node.firstChild)
        node.replaceChild(text,node.firstChild)
    else
        node.appendChild(text);
}

/****************************************************************************/
/****************************************************************************/

var xului_ref = "";
function XulUI()
{
    this.url = null;

    // Internal parms
    this.str = $("webui_strings");
    this.__msg_id = 0;
    this.message_time = 4000;
    this.config = Array();
    this.config["refresh"] = "0";
    this.refreshEvent = null;

    xului_ref = this;
    this.ref = 'xului_ref';

    this.init = function()
    {
        // try to get preference
        var prefManager =
            Components.classes["@mozilla.org/preferences-service;1"]
            .getService(Components.interfaces.nsIPrefBranch);
        try {
            var current = prefManager.getCharPref(
                    "extensions.deejayd-webui.current_server");
            }
        catch (ex) {
            this.display_message(this.getString("prefError"), 'error');
            return;
            }

        if (current != "") { this.url = "http://"+current+"/"; }
        else {
            this.display_message(this.getString("prefError2"), 'error');
            return;
            }

        // set refresh if needed
        var use_default = prefManager.getBoolPref(
                    "extensions.deejayd-webui.use_default_refresh");
        if (!use_default) {
            var refresh = prefManager.getIntPref(
                    "extensions.deejayd-webui.refresh");
            this.setRefresh(refresh);
            }

        this.rpc = new RPC(this, this.url+'rpc/');
        this.rpc.callbacks = {
            updateMode: this.updateStatus,
            updateOption: this.updateStatus,
            updateRating: this.updateStatus,
            queue: this.updateStatus,
            dvd: this.updateStatus,
            player: { def: this.updateStatus, },
            webradio: { def: this.updateStatus, },
            playlist: {
                def: this.updateStatus,
                save: function(data) {
                    xului_ref.displayMessage(xului_ref.getString("plsSave"));
                    xului_ref.updateRecPlaylist();
                }
            },
            panel: { def: this.updateStatus, },
            video: { def: this.updateStatus, },
            recpls: this.updateRecPlaylist,
        };
        this.rpc.onerror = function(request, error, exception) {
            xului_ref.displayMessage("Fatal Error "+ error + " : "+
                request.responseText, 'error');
        };
        this.rpc.onrequesterror = function(code, message){
            xului_ref.displayMessage("Request Error "+ code + " : "+
                message, 'error');
        };

        this.ui = new UI(this);
        this.refresh();
    };

    this.refresh = function()
    {
        this.updateStats();
        this.updateStatus();
        this.updateRecPlaylist();
    };

    this.updateStatus = function(data)
    {
        var status_cb = function(data) { xului_ref.ui.updateStatus(data); };
        xului_ref.rpc.send("status", [], status_cb);
    };

    this.updateStats = function(data)
    {
        var stats_cb = function(data) { xului_ref.ui.updateStats(data); };
        xului_ref.rpc.send("stats", [], stats_cb);
    };

    this.updateRecPlaylist = function(data)
    {
        xului_ref.ui.rec_pls.update();
    };

    this.getString = function(str)
    {
        return this.str.getString(str);
    };

    this.getFormattedString = function(str, values)
    {
        return this.str.getFormattedString(str, values);
    };

    this.__get_message_id = function()
    {
        this.__msg_id += 1;
        return this.__msg_id;
    };

    this.displayMessage = function(msg,type)
    {
        var notif_box = $("notification-box");
        // first remove all notifications
        notif_box.removeAllNotifications(true);

        var p = type == "error" ? 8 : 4;
        var image = "chrome://deejayd-webui/skin/images/";
        image += type == "error" ? "error.png" : "info.png";
        var msg_id = this.__get_message_id();

        notif_box.appendNotification(msg, msg_id, image, p, null);
        if (type != 'error') {
            setTimeout(this.ref+'.hideMessage('+msg_id+')',this.message_time);
            }
    };

    this.hideMessage = function(msg_id)
    {
        var notif_box = $("notification-box");
        var msg = notif_box.getNotificationWithValue(msg_id);
        if (msg != null) {
            try { notif_box.removeNotification(msg); }
            catch (ex) { }
            }
    };

    this.parseConfig = function(config)
    {
        var args = config.getElementsByTagName("arg");
        for (var i=0;arg = args.item(i);i++)
            this.config[arg.getAttribute("name")] = arg.getAttribute("value");

        // set refresh
        var prefManager =
            Components.classes["@mozilla.org/preferences-service;1"]
            .getService(Components.interfaces.nsIPrefBranch);
        var use_default = prefManager.getBoolPref(
                    "extensions.deejayd-webui.use_default_refresh");
        if (use_default)
            this.setRefresh(this.config["refresh"]);
    };

    this.setRefresh = function(refresh)
    {
        if (this.refreshEvent) {
            clearInterval(this.refreshEvent);
            this.refreshEvent = null;
            }
        if (refresh != "0")
            this.refreshEvent = setInterval(
                "xului_ref.updateStatus()", refresh*'1000');
    };
}

window.onload = function(e) {
    var _xului = new XulUI();
    _xului.init();
};

// vim: ts=4 sw=4 expandtab
