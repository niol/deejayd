/*
 * main.js
 */

/****************************************************************************/
/* Common functions
/****************************************************************************/

function $(id) {
  return document.getElementById(id);
}

function toogleNodeVisibility(node)
{
    if (typeof node == 'string')
        node = $(node);

    var newState = node.style.visibility == "visible" ? "collapse" : "visible";
    node.style.visibility = newState;
}

function removeNode(node)
{
	if (typeof node == 'string')
		node = $(node);

	if (node && node.parentNode)
		return node.parentNode.removeChild(node);
	else
		return false;
}

function replaceNodeText(node,content)
{
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
var ajaxdj_ref;
var hasPrivilege = true;
try {
    netscape.security.PrivilegeManager.
        enablePrivilege("UniversalXPConnect");
    }
catch (ex) {
    hasPrivilege = false;
    }


function ajaxdj()
{
    this.playerObj = new Player();
    this.current_msg = null;
    // Activate Debug
    this.debug = false;
    // Initiate debug
    if (this.debug)
        $("debug-button").style.display = "block";

    // Internal parms
    this.localeStrings = Array();
    this.message_time = 4000;
    this.config = Array();
    this.config["refresh"] = "0";
    this.refreshEvent = null;

    ajaxdj_ref = this;
    this.ref = 'ajaxdj_ref';

    this.init = function()
    {
        // Send Init request
        this.send_command('init',null,true);
    };

    this.set_busy = function(a)
    {
        if (a)
            $('msg-loading').style.display = "block";
        else if (!a && this.busy)
            $('msg-loading').style.display = "none";
        this.busy = a;
    };

    this.display_message = function(msg,type)
    {
        var p = type == "error" ? 8 : 4;
        var image = "./static/themes/default/images/";
        image += type == "error" ? "error.png" : "info.png";
        var msg = $("notification-box").appendNotification(msg, 0, image, p);
        this.current_msg = msg;

        if (type != 'error') {
            setTimeout(this.ref+'.hide_message()', this.message_time);
            }
    };

    this.hide_message = function()
    {
        if (this.current_msg != null) {
            $("notification-box").removeNotification(this.current_msg);
            this.current_msg = null;
            }
    };

    this.http_sockets = new Array();

    this.get_request_obj = function()
    {
        for (var n=0; n<this.http_sockets.length; n++) {
            if (!this.http_sockets[n].busy)
                return this.http_sockets[n];
            }

        var i = this.http_sockets.length;
        this.http_sockets[i] = new http_request();

        return this.http_sockets[i];
    };

    this.send_http_request = function(type, url, parm, lock)
    {
        var request_obj = this.get_request_obj();

        if (request_obj) {
            if (lock) this.set_busy(true);

            request_obj.__lock = lock ? true : false;
            request_obj.onerror = function(o){ ajaxdj_ref.http_error(o); };
            request_obj.oncomplete = function(o){
                    ajaxdj_ref.http_response(o); };
            if (type == 'GET')
                request_obj.GET(url);
            else
                request_obj.POST(url,parm);
            }
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

    this.http_error = function(request_obj)
    {
        this.display_message('Error '+ request_obj.responseStatus +
            ' in request : '+request_obj.url, 'error');

        if (request_obj.__lock)
            this.set_busy(false);

        request_obj.reset();
        request_obj.__lock = false;
    };

    this.http_response = function(request_obj)
    {
        if (request_obj.__lock)
            this.set_busy(false);

        this.set_debug(request_obj.responseText);
        var rs = '';
        var xmldoc = request_obj.responseXML;
        if (xmldoc)
        {
            rs = xmldoc.getElementsByTagName("config").item(0);
            if (rs)
                this.parseConfig(rs);

            rs = xmldoc.getElementsByTagName("locale").item(0);
            if (rs)
                this.parseLocale(rs);

            rs = xmldoc.getElementsByTagName("message").item(0);
            if (rs)
                this.display_message(rs.firstChild.data,
                    rs.getAttribute("type"));

            rs = xmldoc.getElementsByTagName("availableModes").item(0);
            if (rs) {
                // queue always need to be loaded
                this.quObj = new Queue();
                this.quObj.init();

                var modes = rs.getElementsByTagName("mode");
                for(var i=0; mode = modes.item(i); i++) {
                    if (mode.getAttribute("activate") == "1") {
                        switch (mode.getAttribute("name")) {
                            case "playlist":
                            this.fileListObj = new FileList();
                            this.fileListObj.init();
                            this.plObj = new Playlist();
                            this.plObj.init();
                            break;

                            case "panel":
                            this.panelObj = new Panel();
                            this.panelObj.init();
                            break;

                            case "webradio":
                            this.webradioObj = new Webradio();
                            this.webradioObj.init();
                            break;

                            case "video":
                            this.videoList = new VideoList();
                            this.videoLib = new VideoLibrary();
                            break;

                            case "dvd":
                            this.dvdObj = new Dvd();
                            this.dvdObj.init();
                            break;
                            }
                        }
                    }
                playerStatus.init_mode();
                }

            rs = xmldoc.getElementsByTagName("setsource").item(0);
            if (rs)
            {
                var mode = rs.getAttribute("value");
                var selectedSrc = 0;
                if (mode == "panel")
                    selectedSrc = 1;
                else if (mode == "webradio")
                    selectedSrc = 2;
                else if (mode == "video")
                    selectedSrc = 3;
                else if (mode == "dvd")
                    selectedSrc = 4;

                $('main').selectedIndex = selectedSrc;
                $('mode-menu').value = mode;
            }

            rs = xmldoc.getElementsByTagName("audio_update").item(0);
            if (rs)
                this.fileListObj.updateDatabase(rs);
            rs = xmldoc.getElementsByTagName("video_update").item(0);
            if (rs)
                this.videoLib.updateDatabase(rs);

            rs = xmldoc.getElementsByTagName("playlist").item(0);
            if (rs)
                this.plObj.update(rs);

            rs = xmldoc.getElementsByTagName("file-list").item(0);
            if (rs)
                this.fileListObj.updateFileList(rs,
                    rs.getAttribute("directory"));

            rs = xmldoc.getElementsByTagName("audiosearch-list").item(0);
            if (rs)
                this.fileListObj.updateFileList(rs, "");

            rs = xmldoc.getElementsByTagName("webradio").item(0);
            if (rs)
                this.webradioObj.update(rs);

            rs = xmldoc.getElementsByTagName("playlist-list").item(0);
            if (rs) {
                if (this.fileListObj)
                    this.fileListObj.updatePlaylistList(rs);
                if (this.panelObj)
                    this.panelObj.updatePlaylistList(rs);
                if (this.plObj)
                    this.plObj.updatePlaylistList(rs);
                this.quObj.updatePlaylistList(rs);
                }

            rs = xmldoc.getElementsByTagName("queue").item(0);
            if (rs)
                this.quObj.update(rs);

            rs = xmldoc.getElementsByTagName("panel").item(0);
            if (rs)
                this.panelObj.update(rs);

            rs = xmldoc.getElementsByTagName("dvd").item(0);
            if (rs)
                this.dvdObj.update(rs);

            rs = xmldoc.getElementsByTagName("video").item(0);
            if (rs)
                this.videoList.update(rs);

            rs = xmldoc.getElementsByTagName("videodir").item(0);
            if (rs)
                this.videoLib.updateDir(rs);

            rs = xmldoc.getElementsByTagName("player").item(0);
            if (rs)
                this.playerObj.updatePlayerInfo(rs);
        }
        else
            alert(request_obj.responseText);

        return;
    };

    this.updateMode = function()
    {
        this.send_command("setMode",{mode:$('mode-menu').value},true);
    }

    this.parseConfig = function(config)
    {
        var args = config.getElementsByTagName("arg");
        for (var i=0;arg = args.item(i);i++)
            this.config[arg.getAttribute("name")] = arg.getAttribute("value");

        // Reload refresh
        if (this.refreshEvent) {
            clearInterval(this.refreshEvent);
            this.refreshEvent = null;
            }
        if (this.config["refresh"] != "0")
            this.refreshEvent = setInterval(
                "ajaxdj_ref.send_command('refresh','',false)",
                this.config["refresh"]*'1000');
    };

    this.parseLocale = function(locale)
    {
        var strings = locale.getElementsByTagName("strings");
        for (var i=0;str = strings.item(i);i++)
            this.localeStrings[str.getAttribute("name")] =
                str.getAttribute("value");
    };

    this.getString = function(str)
    {
        if (this.localeStrings[str])
            return this.localeStrings[str];
        else
            return "";
    };

    this.set_debug = function(msg)
    {
        if (this.debug) $('debug').value = msg;
    };

    this.toggleDebugZone = function()
    {
        var obj = $("main-and-debug");
        if (obj.selectedIndex == 0)
            obj.selectedIndex = 1;
        else
            obj.selectedIndex = 0;
    };
}

//
//general functions
//
function updatePlaylistMenu(menu_id, playlistList, command_ref)
{
    var menu = $(menu_id);
    // first remove old playlist
    while(menu.hasChildNodes())
        menu.removeChild(menu.firstChild);

    var playlists = playlistList.getElementsByTagName("item");
    for (var i=0;pls=playlists[i];i++) {
        var item = document.createElement("menuitem");
        item.setAttribute("label",pls.firstChild.data);
        if (command_ref) {
            item.setAttribute("oncommand",
                command_ref+".addToPlaylist('"+pls.getAttribute("id")+"');");
            }
        menu.appendChild(item);
        }
};

window.onload = function(e)
{
    var _ajaxdj = new ajaxdj();
    _ajaxdj.init();
};
