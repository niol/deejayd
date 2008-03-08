// player.js

var player_ref;

var Player = function()
{
    player_ref = this;

    this.updatePlayerInfo = function(playerObj)
    {
        // Update option buttons
        var options = Array("random","repeat");
        for (var opt in options) {
            var opt_obj = playerObj.getElementsByTagName(options[opt]).item(0);
            if (opt_obj)
                $(options[opt]+"-button").checked =
                    opt_obj.firstChild.data == "1" ?  true : false;
            }

        // Update Volume
        var vol = playerObj.getElementsByTagName("volume").item(0)
        $('player-volume').updateVolume(vol.firstChild.data);
        $('volume-image').src = "./static/themes/default/images/volume-max.png";

        // Remove current media infos
        var media_info = $("media-info");
        while (media_info.hasChildNodes())
            removeNode(media_info.firstChild);

        var state = playerObj.getElementsByTagName("state").item(0).
                        firstChild.data;
        if (state == "stop") {
            $("playtoggle-button").className = "play-button";

            var rows = Array("audio-row", "subtitle-row", "av_offset-row",
                "sub_offset-row", "player-seekbar", "current-media");
            for (ix in rows) {
                $(rows[ix]).style.visibility = "collapse";
                }
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

                a = Array("av_offset","sub_offset");
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
        }

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
        ajaxdj_ref.send_command('setPlayerOption',{option_name:"audio_lang",
            option_value: idx},true);
    }

    this.set_slang = function(idx)
    {
        ajaxdj_ref.send_command('setPlayerOption',{option_name:"sub_lang",
            option_value: idx},true);
    }

    this.set_avoffset = function()
    {
        ajaxdj_ref.send_command('setPlayerOption',{option_name:"av_offset",
            option_value: $("av_offset-value").value},true);
    }

    this.set_suboffset = function()
    {
        ajaxdj_ref.send_command('setPlayerOption',{option_name:"sub_offset",
            option_value: $("sub_offset-value").value},true);
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
        $(type+"-row").style.visibility = "visible";
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
