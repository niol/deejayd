// player.js

var player_ref;

var Player = function()
{
    player_ref = this;

    this.updatePlayerInfo = function(playerObj)
    {
        // Update Volume
        var vol = playerObj.getElementsByTagName("volume").item(0).
                    firstChild.data;
        $('player-volume').updateVolume(vol);
        $('volume-image').src = "./static/themes/default/images/volume-max.png";

        // Update Current Song
        // first we remove current media infos
        var media_info = $("media-info");
        while (media_info.hasChildNodes())
            removeNode(media_info.firstChild);
        $("audio-menubox").style.visibility = "collapse";
        $("subtitle-menubox").style.visibility = "collapse";

        var state = playerObj.getElementsByTagName("state").item(0).
                        firstChild.data;
        if (state == "stop") {
            $("player-seekbar").style.visibility = "collapse";
            $("playtoggle-button").className = "play-button";
            }
        else if (state == "play")
            $("playtoggle-button").className = "pause-button";
        else if (state == "pause")
            $("playtoggle-button").className = "play-button";

        // Now we try to obtain current song info
        var cur_song = playerObj.getElementsByTagName("cursong").item(0);
        if (cur_song) {
            switch(cur_song.getAttribute("type")) {
                case "song":
                // title
                this.__build_title(cur_song);
                // Artist
                var artist = cur_song.getElementsByTagName("artist").item(0);
                if (artist.firstChild)
                    this.__build_label_item("artist",artist.firstChild.data);
                // Album
                var album = cur_song.getElementsByTagName("album").item(0);
                if (album.firstChild)
                    this.__build_label_item("album",album.firstChild.data);
                break;

                case "webradio":
                // title
                var title = cur_song.getElementsByTagName("title").item(0).
                    firstChild.data;
                var song = cur_song.getElementsByTagName("song-title").item(0);
                if (song)
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
                break;
                }
            $("current-song").style.visibility = "visible";
        }
        else
            $("current-song").style.visibility = "collapse";

        // Update Time
        var value = "0:00";
        var seekbarValue = 0;
        var time = playerObj.getElementsByTagName("time").item(0);
        if (time) {
            time = time.firstChild.data;
            time = time.split(":");
            value = formatTime(time[0]);
            seekbarValue = (time[0] / time[1]) * 100;
            this.songTime = time[1];
            }
        $('seekbar-button').label = value + " -->";
        $('player-seekbar').updateSeekbar(seekbarValue);

        // Update option buttons
        var options = Array("random","repeat");
        for (var opt in options) {
            var opt_obj = playerObj.getElementsByTagName(options[opt]).item(0);
            if (opt_obj)
                $(options[opt]+"-button").checked =
                    opt_obj.firstChild.data == "1" ?  true : false;
            }
    };

    this.showSeekbar = function()
    {
        var seekbar = $('player-seekbar');
        var newState = seekbar.style.visibility == "collapse" ?
                        "visible" : "collapse";
        seekbar.style.visibility = newState;
    };

    this.goToCurSong = function()
    {
        if (this.currSong) {
            var tree = $("playlist-tree");
            var boxobject = tree.treeBoxObject;
            boxobject.ensureRowIsVisible(this.currSong.pos);
            }
    };

    this.set_alang = function(idx)
    {
        ajaxdj_ref.send_command('setAlang',{lang_idx: idx},true);
    }

    this.set_slang = function(idx)
    {
        ajaxdj_ref.send_command('setSlang',{lang_idx: idx},true);
    }

    //
    // Internal Functions
    //
    this.__build_menu = function(type,obj,current_channel)
    {
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
        $(type+"-menubox").style.visibility = "visible";
    };

    this.__build_title = function(current_song)
    {
        var title = current_song.getElementsByTagName("title").item(0);
        if (!title.firstChild)
            title = current_song.getElementsByTagName("filename").item(0);
        title = title.firstChild.data;

        var length = current_song.getElementsByTagName("length").item(0);
        if (length)
            title += " (" + formatTime(length.firstChild.data) + ")";

        this.__build_label_item("title",title);
    };

    this.__build_label_item = function(type,val)
    {
        var desc = document.createElement("description");
        desc.id = "current-"+type;
        desc.className = "cursong";
        desc.appendChild(document.createTextNode(val));
        $("media-info").appendChild(desc);
    };

};


var PlayerObserver =
{
    volume_timeout: null,

    onTrackVolume: function(obj)
    {
        if (this.volume_timeout)
            clearTimeout(this.volume_timeout);

        obj.trackingVolume = true;
        this.volume_timeout = setTimeout(
            "ajaxdj_ref.send_command('setVol',{volume:"+obj.value+
                "},true)", 200);
    },

    onReleaseVolume: function(obj)
    {
        if (this.volume_timeout)
            clearTimeout(this.volume_timeout);

        obj.trackingVolume = false;
        ajaxdj_ref.send_command('setVol',{volume: obj.value},true);
    },

    onTrackSeekbar: function(obj)
    {
        obj.trackingPosition = true;

        var timeVal = parseInt( (Number(obj.value)*Number(player_ref.songTime))
                        / 100 );
        $('seekbar-button').label = formatTime(timeVal) + " -->";
    },

    onReleaseSeekbar: function(obj)
    {
        obj.trackingPosition = false;
        var timeVal = parseInt( (Number(obj.value)*Number(player_ref.songTime))
                        / 100 );
        ajaxdj_ref.send_command('setTime',{time: timeVal},true);
    }

};
