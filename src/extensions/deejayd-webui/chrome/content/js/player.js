// player.js

var playerStatus = {
    volume: "",
    update_volume: function() {
        $('player-volume').value = this.volume;
        $('volume-image').src = "chrome://deejayd-webui/skin/"+
            "images/volume-max.png";
        },

    queueplayorder: "",
    update_queueplayorder: function() {
        $("queue-playorder").checked = this.queueplayorder == "random" ?
                                      true : false;
        },

    playlistrepeat: "",
    update_playlistrepeat: function() {
        $("playlist-repeat").checked = this.playlistrepeat == "1" ?
                                       true : false;
        },

    playlistplayorder: "",
    update_playlistplayorder: function() {
        $("playlist-playorder").value = this.playlistplayorder;
        },

    videorepeat: "",
    update_videorepeat: function() {
        $("video-repeat").checked = this.videorepeat == "1" ?  true : false;
        },

    videoplayorder: "",
    update_videoplayorder: function() {
        $("video-playorder").value = this.videoplayorder;
        },

    panelrepeat: "",
    update_panelrepeat: function() {
        $("panel-repeat").checked = this.panelrepeat == "1" ?  true : false;
        },

    panelplayorder: "",
    update_panelplayorder: function() {
        $("panel-playorder").value = this.panelplayorder;
        },

    state: "",
    update_state: function() {
        $("playtoggle-button").className = this.state == "play" ?
                                           "pause-button" : "play-button";
        },

    /********************************************************************/
    /********************************************************************/
    time: "",
    media_length:"",
    update_time: function(t) {
        this.time = t;
        var seekbarValue = 0;
        var time = this.time.split(":");
        this.media_length = time[1];
        value = formatTime(time[0]);
        seekbarValue = (time[0] / time[1]) * 100;
        $('seekbar-button').label = value + " -->";
        $('player-seekbar').max = time[1];
        $('player-seekbar').value = time[0];
        },

    init_mode: function() {
        this.modes = {};
        this.modes["playlist"] = playlist_ref;
        this.modes["webradio"] = webradio_ref;
        this.modes["video"] = videolist_ref;
        this.modes["panel"] = panel_ref;
        this.modes["dvd"] = dvd_ref;
        },
    current: "",
    current_mode: null,
    current_in_queue: false,
    reset_current: function() {
        var media_info = $("media-info");
        while (media_info.hasChildNodes())
            removeNode(media_info.firstChild);
        // hide option block
        var rows = Array("audio-row", "subtitle-row", "av_offset-row",
            "sub_offset-row", "zoom-row",  "player-seekbar", "current-media",
            "playeroption-button");
        for (ix in rows) {
            $(rows[ix]).style.visibility = "collapse";
            }

        $("queue-status-button").className = "stop-button";
        this.current_in_queue = false;
        if (this.current_mode) {
            this.modes[this.current_mode].resetPlaying();
            this.current_mode = null;
            }
        // hide cover
        $("cover-img").style.visibility = "collapse";
        },
    __update_current_state: function() {
        var current = this.current.split(":");
        if (current[2] == "queue") {
            $("queue-status-button").className = this.state+"-button";
            this.current_in_queue = true;
            }
        else {
            this.modes[current[2]].setPlaying(current[0],current[1],this.state);
            this.current_mode = current[2];
            }
        },
    update_current: function(cur_song) {
        this.reset_current();
        this.__update_current_state();

        switch(cur_song.getAttribute("type")) {
            case "song":
            $("playeroption-button").style.visibility = "collapse";
            // title
            this.__build_title(cur_song);
            // Artist
            var artist = cur_song.getElementsByTagName("artist").item(0);
            if (artist && artist.firstChild)
                this.__build_label_item("artist",artist.firstChild.data);
            // Album
            var album = cur_song.getElementsByTagName("album").item(0);
            if (album && album.firstChild)
                this.__build_label_item("album",album.firstChild.data);
            // Cover
            var cover = cur_song.getElementsByTagName("cover").item(0);
            if (cover && cover.firstChild) {
                $('cover-img').src=ajaxdj_ref.url+"rdf/"+cover.firstChild.data;
                $('cover-img').style.visibility = "visible";
                }
            break;

            case "webradio":
            $("playeroption-button").style.visibility = "collapse";
            // title
            var title = cur_song.getElementsByTagName("title").item(0).
                firstChild.data;
            var song = cur_song.getElementsByTagName("song-title").item(0);
            if (song && song.firstChild)
                title += " : " + song.firstChild.data;
            this.__build_label_item("title", title);
            // Url
            var url = cur_song.getElementsByTagName("url").item(0);
            if (url)
                this.__build_label_item("url",url.firstChild.data);
            break;

            case "video":
            // title
            this.__build_title(cur_song);

            var a = Array("audio","subtitle");
            for (ix in a) {
                var obj = cur_song.getElementsByTagName(a[ix]).item(0);
                var cur_ch = cur_song.getElementsByTagName(a[ix]+
                        "_idx").item(0);
                if (obj && cur_ch) {
                    this.__build_menu(a[ix],obj,cur_ch.firstChild.data);
                    }
                }

            a = Array("av_offset","sub_offset", "zoom");
            for (ix in a) {
                var value = cur_song.getElementsByTagName(a[ix]).item(0);
                if (value && value.firstChild) {
                    $(a[ix]+"-row").style.visibility = "visible";
                    $(a[ix]+"-value").value = value.firstChild.data;
                    }
                }
            $("playeroption-button").style.visibility = "visible";
            break;
            }
        $("current-media").style.visibility = "visible";

        },
    update_current_option: function(current_obj) {
        if (this.current_in_queue)
            $("queue-status-button").className = this.state+"-button";
        else if (this.current_mode)
            this.modes[this.current_mode].updatePlaying(this.state);
        },

    //
    // Internal Functions
    //
    __build_menu: function(type, obj, current_channel) {
        var menu = $(type+"-menu");
        // first clear old menu
        while (menu.hasChildNodes())
            removeNode(menu.firstChild);

        var current_item = null;
        var items = obj.getElementsByTagName("dictparm");
        for(var i = 0;item = items[i];i++) {
            var it = document.createElement("menuitem");
            it.setAttribute("label",item.getAttribute('lang'));
            it.setAttribute("value",item.getAttribute('ix'));
            menu.appendChild(it);

            if (item.getAttribute('ix') == current_channel)
                current_item = it;
            }

        if (current_item)
            menu.parentNode.selectedItem = current_item;
        $(type+"-row").style.visibility = "visible";
        },

    __build_title: function(current_song) {
        var title = current_song.getElementsByTagName("title").item(0);
        if (!title || !title.firstChild)
            title = current_song.getElementsByTagName("filename").item(0);
        title = title.firstChild.data;

        var length = current_song.getElementsByTagName("length").item(0);
        if (length)
            title += " (" + formatTime(length.firstChild.data) + ")";

        this.__build_label_item("title",title);
        },

    __build_label_item: function(type,val) {
        var desc = document.createElement("description");
        desc.id = "current-"+type;
        desc.className = "cursong";
        desc.appendChild(document.createTextNode(val));
        $("media-info").appendChild(desc);
        },
    };


var player_ref;
var Player = function()
{
    player_ref = this;

    this.updatePlayerInfo = function(playerObj)
    {
        // extract status infos
        parm_objs = playerObj.getElementsByTagName("parm");
        obj = "";
        st_obj = new Object();
        for(var i=0; obj = parm_objs.item(i); i++)
            st_obj[obj.getAttribute("key")] = obj.getAttribute("value");

        var list = Array("state","volume","playlistplayorder",
            "playlistrepeat","videoplayorder","videorepeat",
            "queueplayorder","panelplayorder","panelrepeat");
        for (var i in list) {
            var key = list[i];
            if (st_obj[key] && st_obj[key] != playerStatus[key]) {
                playerStatus[key] = st_obj[key];
                playerStatus["update_"+key]();
                }
            }
        var time = "time" in st_obj ? st_obj["time"] : "0:0";
        playerStatus["update_time"](time);

        // update current song
        if ("current" in st_obj) {
            var cur_song = playerObj.getElementsByTagName("cursong").item(0);
            if (st_obj["current"] != playerStatus.current) {
                playerStatus.current = st_obj["current"];
                playerStatus.update_current(cur_song);
                }
            else {
                var song = cur_song.getElementsByTagName("song-title").item(0);
                if (song && song.firstChild) // it is a webradio
                    playerStatus.update_current(cur_song);
                else
                    playerStatus.update_current_option(cur_song);
                }
            }
        else if (playerStatus.current != "") {
            playerStatus.reset_current();
            playerStatus.current = "";
            }
    };

    this.set_alang = function(idx)
    {
        ajaxdj_ref.send_command('setPlayerOption',{option_name:"audio_lang",
            option_value: idx},true);
    };

    this.set_slang = function(idx)
    {
        ajaxdj_ref.send_command('setPlayerOption',{option_name:"sub_lang",
            option_value: idx},true);
    };

    this.set_avoffset = function()
    {
        ajaxdj_ref.send_command('setPlayerOption',{option_name:"av_offset",
            option_value: $("av_offset-value").value},true);
    };

    this.set_suboffset = function()
    {
        ajaxdj_ref.send_command('setPlayerOption',{option_name:"sub_offset",
            option_value: $("sub_offset-value").value},true);
    };

    this.set_zoom = function()
    {
        ajaxdj_ref.send_command('setPlayerOption',{option_name:"zoom",
            option_value: $("zoom-value").value},true);
    };
};


var PlayerObserver =
{
    volume_timeout: null,
    seek_timeout: null,

    volumeUpdate: function(obj)
    {
        if (this.volume_timeout) {
            clearTimeout(this.volume_timeout);
            this.volume_timeout = null;
            }

        if (parseInt(obj.value) != parseInt(playerStatus.volume))
            this.volume_timeout = setTimeout(
                "ajaxdj_ref.send_command('setVol',{volume:"+obj.value+
                    "},true)", 300);
    },

    seekUpdate: function(obj)
    {
        if (this.seek_timeout) {
            clearTimeout(this.seek_timeout);
            this.seek_timeout = null;
            }

        var time = playerStatus.time.split(":");
        if (parseInt(obj.value) != parseInt(time[0])) {
            $('seekbar-button').label = formatTime(obj.value) + " -->";
            this.seek_timeout = setTimeout(
                "ajaxdj_ref.send_command('setTime',{time: "+obj.value+
                "},true);", 300);
            }
    },
};
