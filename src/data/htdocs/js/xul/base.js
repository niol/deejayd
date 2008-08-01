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

function is_supported() {
    try {
        netscape.security.PrivilegeManager.
            enablePrivilege("UniversalXPConnect");
        }
    catch (ex) {
        // return error message
        }
}

var UIController = function(mainController)
{
    this.current_msg = null;
    this.mainController = mainController;
    // Init var
    this.playerObj = new Player();
    // Initiate debug
    if (mainController.debug)
        $("debug-button").style.display = "block";

    this.set_busy = function(a)
    {
        var state = a ? "block" : "none";
        $('msg-loading').style.display = state;
    };

    this.display_message = function(msg, type)
    {
        var p = type == "error" ? 8 : 4;
        var image = "./static/themes/default/images/";
        image += type == "error" ? "error.png" : "info.png";

        var msg = $("notification-box").appendNotification(msg, 0, image, p);
        this.current_msg = msg;
    };

    this.hide_message = function()
    {
        if (this.current_msg != null) {
            $("notification-box").removeNotification(this.current_msg);
            this.current_msg = null;
            }
    };

    this.set_debug = function(msg)
    {
        if (this.mainController.debug) $('debug').value = msg;
    };

    this.parseXMLAnswer = function(xmldoc)
    {
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
    };

/************************************************/
/************************************************/
    this.toggleDebugZone = function()
    {
        var obj = $("main-and-debug");
        if (obj.selectedIndex == 0)
            obj.selectedIndex = 1;
        else
            obj.selectedIndex = 0;
    };
}

// vim: ts=4 sw=4 expandtab
