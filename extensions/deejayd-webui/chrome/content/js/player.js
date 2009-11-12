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

function Player()
{
    this._volume = -1;
    this._volume_timeout = null,
    this._state = "stop";
    this._time = null;
    this._seek_timeout = null,
    this._current = "";
    this._vol_images = {
        max: "chrome://deejayd-webui/skin/images/volume-max.png",
    };

    return this;
}

Player.prototype =
{
    update: function(st) {
        var player = xului_ref.ui.player;

        // update state
        if (st.state != player._state) {
            $("playtoggle-button").className = st.state == "play" ?
                "pause-button" : "play-button";
            player._state = st.state;
        }

        // update volume
        if (st.volume != player._volume) {
            $('player-volume').value = st.volume;
            $('volume-image').src = player._vol_images.max;
            player._volume = st.volume;
        }

        // update current song
        if (st.state != "stop") {
            if (st.current != player._current) {
                player.updateCurrent(st.current);
                player._current = st.current;
            }
            else {
                player.updateCurrentState(st.current);
            }
            // update time
            if (this._time != st.time) {
                this._time = st.time;
                var time = st.time.split(":");
                $('seekbar-button').label = formatTime(time[0]) + " -->";
                $('player-seekbar').max = time[1];
                $('player-seekbar').value = time[0];
            }
        }
        else if (player._current != "") {
            player.resetCurrent();
            player._current = "";
        }
        else
            this._time = null;
    },

    volumeUpdate: function(obj) {
        if (this._volume_timeout) {
            clearTimeout(this._volume_timeout);
            this._volume_timeout = null;
        }

        if (parseInt(obj.value) != parseInt(this._volume))
            this._volume_timeout = setTimeout(
                    "xului_ref.rpc.setVolume("+obj.value+")", 300);
    },

    seekUpdate: function(obj) {
        if (this._seek_timeout) {
            clearTimeout(this._seek_timeout);
            this._seek_timeout = null;
        }

        if (this._time) {
            var time = this._time.split(":");
            if (parseInt(obj.value) != parseInt(time[0])) {
                $('seekbar-button').label = formatTime(obj.value) + " -->";
                this._seek_timeout = setTimeout(
                        "xului_ref.rpc.seek("+obj.value+", false)", 300);
            }
        }
    },

    setAlang: function(idx) {
        xului_ref.rpc.setPlayerOption("audio_lang", idx);
    },

    setSlang: function(idx) {
        xului_ref.rpc.setPlayerOption("sub_lang", idx);
    },

    setAspectRatio: function(aspect) {
        xului_ref.rpc.setPlayerOption("aspect_ratio", aspect);
    },

    setAVOffset: function() {
        xului_ref.rpc.setPlayerOption("av_offset", $("av_offset-value").value);
    },

    setSubOffset: function() {
        xului_ref.rpc.setPlayerOption("sub_offset",$("sub_offset-value").value);
    },

    setZoom: function() {
        xului_ref.rpc.setPlayerOption("zoom",$("zoom-value").value);
    },

/*
 * Current update
 */
    resetCurrent: function() {
        var media_info = $("media-info");
        while (media_info.hasChildNodes())
            removeNode(media_info.firstChild);
        // hide option block
        var rows = Array("audio-row", "subtitle-row", "av_offset-row",
            "sub_offset-row", "zoom-row",  "aspect_ratio-row",
            "player-seekbar", "current-media", "playeroption-button");
        for (ix in rows) {
            $(rows[ix]).style.visibility = "collapse";
            }

        $("queue-status-button").className = "stop-button";
        if (this._current) {
            cur_state = this._current.split(":");
            if (cur_state[2] != "queue")
                xului_ref.ui.modes[cur_state[2]].resetPlaying();
            }
        // hide cover
        $("cover-img").style.visibility = "collapse";
        },

    updateCurrent: function(cur_state) {
        var player = this;
        var callback = function(data) {
            var current = data.medias[0];
            switch(current.type) {
                case "song":
                    $("playeroption-button").style.visibility = "collapse";
                    // title
                    player.__build_title(current);
                    // Artist
                    if (current.artist)
                        player.__build_label_item("artist", current.artist);
                    // Album
                    if (current.album)
                        player.__build_label_item("album", current.album);
                    // Cover
                    var cover_callback = function(data) {
                        if (data.cover) {
                            $('cover-img').src=xului_ref.url+data.cover;
                            $('cover-img').style.visibility = "visible";
                        }
                    };
                    xului_ref.rpc.send("web.writecover",[current.media_id],
                            cover_callback);
                break;

                case "webradio":
                    $("playeroption-button").style.visibility = "collapse";
                    // title
                    var title = current.title;
                    if (current["song-title"])
                        title += " : " + current["song-title"];
                    player.__build_label_item("title", title);
                    // Url
                    if (current.uri)
                        player.__build_label_item("url",current.uri);
                break;

                case "video":
                    // title
                    player.__build_title(current);
                    player.__updateVideoOptions(current);
                    $("playeroption-button").style.visibility = "visible";
                break;
            }

            $("current-media").style.visibility = "visible";
        };

        this.resetCurrent();
        cur_state = cur_state.split(":");
        if (cur_state[2] == "queue")
            $("queue-status-button").className = this._state+"-button";
        else
            xului_ref.ui.modes[cur_state[2]].setPlaying(cur_state[0],
                    cur_state[1], this._state);

        xului_ref.rpc.send("player.current", [], callback);
        },

    updateCurrentState: function(cur_state) {
        var cur_state = cur_state.split(":");
        if (cur_state[2] == "queue")
            $("queue-status-button").className = this._state+"-button";
        else
            xului_ref.ui.modes[cur_state[2]].updatePlaying(this._state);

        // if source is webradio or video,
        // current current to update player options
        if (cur_state[2] == "webradio" || cur_state[2] == "video") {
            var player = this;
            var callback = function(data) {
                var current = data.medias[0];
                if (current.type == "video")
                    player.__updateVideoOptions(current);
                if (current.type == "webradio" && current["song-title"]) {
                    var title = current.title + " : " + current["song-title"];
                    var label = $("current-title");
                    label.firstChild.data = title;
                }
            };
            xului_ref.rpc.send("player.current", [], callback);
        }
    },

    //
    // Internal Functions
    //
    __updateVideoOptions: function(current) {
        var a = Array("audio","subtitle");
        for (ix in a) {
            var cur_ch = current[a[ix]+"_idx"];
            if (typeof(current[a[ix]]) != "undefined"
                    && typeof(cur_ch) != "undefined") {
                this.__build_menu(a[ix], current[a[ix]], cur_ch);
            }
        }

        a = Array("av_offset","sub_offset", "zoom", "aspect_ratio");
        for (ix in a) {
            if (typeof(current[a[ix]]) != "undefined") {
                $(a[ix]+"-row").style.visibility = "visible";
                $(a[ix]+"-value").value = current[a[ix]];
            }
        }
    },

    __build_menu: function(type, obj, current_channel) {
        var menu = $(type+"-menu");
        // first clear old menu
        while (menu.hasChildNodes())
            removeNode(menu.firstChild);

        var current_item = null;
        for(var i = 0;channel = obj[i];i++) {
            var it = document.createElement("menuitem");
            it.setAttribute("label", channel.lang);
            it.setAttribute("value", channel.ix);
            menu.appendChild(it);

            if (channel.ix == current_channel)
                current_item = it;
            }

        if (current_item)
            menu.parentNode.selectedItem = current_item;
        $(type+"-row").style.visibility = "visible";
    },

    __build_title: function(current) {
        var title = current.title ? current.title : current.filename;
        if (current.length)
            title += " (" + formatTime(parseInt(current.length)) + ")";

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

// vim: ts=4 sw=4 expandtab
