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

var iPhone = RegExp("(iPhone|iPod)").test(navigator.userAgent);

function UI(controller)
{
    this.def_cover = "static/themes/mobile/images/missing-cover.png";
    this.initialize(controller);
    return this;
}

UI.prototype =
{
    initialize: function(controller, url) {
        this._controller = controller;
        this.message_time = 4000;
        this.current_page = {name: "now_playing", obj: null};

        // handler on ajax event
        $("#loading").ajaxStart(function(){
            window.scrollTo(0, 1);
            $(this).show();
        });
        $("#loading").ajaxStop(function(){ $(this).hide(); });

        // initialize pager for medialist
        $(".pager-first").click(function(evt) {
            var mode = mobileui_ref.ui.getCurrentMode();
            if (mode.current_page != 1)
                mode.updateMedialist(mode.current_length, 1);
            });
        $(".pager-previous").click(function(evt) {
            var mode = mobileui_ref.ui.getCurrentMode();
            if (mode.current_page > 1)
                mode.updateMedialist(mode.current_length, mode.current_page-1);
            });
        $(".pager-next").click(function(evt) {
            var mode = mobileui_ref.ui.getCurrentMode();
            if (mode.current_page < mode.total_page)
                mode.updateMedialist(mode.current_length, mode.current_page+1);
            });
        $(".pager-last").click(function(evt) {
            var mode = mobileui_ref.ui.getCurrentMode();
            if (mode.current_page != mode.total_page)
                mode.updateMedialist(mode.current_length, mode.total_page);
            });
    },

    displayMessage: function(msg, type) {
        var cont = msg;
        if (type == 'error')
            cont = '<input type="submit" onclick="mobileui_ref.hide_message();'+
                        ' return false;" value="Close"/>' + cont;
        cont = '<div class="'+type+'">'+cont+'</div>';

        $("#notification").html(cont).show();
        if (type != 'error') {
            setTimeout('mobileui_ref.ui.hideMessage()',
                    mobileui_ref.ui.message_time);
            }
    },

    hideMessage: function() { $("#notification").hide(); },

    buildPage: function(page, st) {
        if (this.current_page.name == page && this.current_page.obj) {
            // just update the page
            this.current_page.obj.update(st);
            return false;
        }
        else if (this.current_page.name != page) {
            $("#"+this.current_page.name+"_page").hide();
            // hide options
            $("#mode-extra").hide();
            $("#mode-main").show();
        }

        switch (page) {
            case "now_playing":
                var obj = new NowPlayingPage(st);
                break;
            case "modelist":
                window.scrollTo(0, 1);
                $("#modelist_page").show();
                var obj = null;
                break;
            case "current_mode":
                var modes = {
                    playlist: PlaylistMode,
                    video: VideoMode,
                    webradio: WebradioMode,
                    dvd: DvdMode,
                    panel: PanelMode,
                };
                var obj = new modes[st.mode](st, this._controller);
                break;
        }
        this.current_page = {name: page, obj: obj};
        return false;
    },

    getCurrentMode: function() {
        if (this.current_page.name == "current_mode")
            return this.current_page.obj;
        return null;
    },
};


//
// Now Playing Page
//
function NowPlayingPage(st) {
    this.initialize(st);
    return this;
}

NowPlayingPage.prototype =
{
    initialize: function(st) {
        // init var
        this._state = "stop";
        this._volume = -1;
        this._current = -1;

        // build page
        this.update(st);
        $("#now_playing_page").show();
    },

    update: function(st) {
        // update play/pause button
        var state = st.state;
        if (state != this._state) {
            $("#playpause_button").removeClass(this._state);
            $("#playpause_button").addClass(state);
            this._state = state;
        }

        // update volume
        var volume = st.volume;
        if (volume != this._volume) {
            var left = parseInt(volume)*2 - 12;
            $("#volume-handle").attr("value", volume);
            $("#volume-handle").css("left", left+"px");
            this._volume = volume;
        }

        // update position
        if (st.state != "stop" && st.mode != "webradio") {
            // parse st.time parameter
            var times = st.time.split(":");
            $("#time-control-position").html(formatTime(times[0]) + "/" +
                    formatTime(times[1]));
            $("#playing-time-control").show();
        }
        else {
            $("#playing-time-control").hide();
        }

        // update current media
        var current = st.current ? st.current : null;
        if (current != this._current) {
            $("#playing-title").empty().html("");
            if (current) {
                // get informations on current media
                var current_callback = function(data) {
                    var media = data.medias[0];
                    if (media) {
                        var playing_text = createElement("div", "",
                                {id: "playing-text"});
                        var title = createElement("div", "title", {});
                        var desc = createElement("div", "desc", {});
                        switch (media.type) {
                            case "song":
                                $(title).html(media.title + " (" +
                                        formatTime(media.length)+ ")");
                                $(desc).html(media.artist+" - "+media.album);
                                break;
                            case "video":
                                $(title).html(media.title + " (" +
                                        formatTime(media.length)+ ")");
                                break;
                            case "webradio":
                                $(title).html(media.title);
                                $(desc).html(media.url);
                                break;
                        }
                        $(playing_text).append(title).append(desc);
                        $("#playing-title").append(playing_text);

                        // get cover if available
                        var cover_callback = function(data) {
                            if (data.cover)
                                $("#playing-cover").attr("src", data.cover);
                            else
                                $("#playing-cover").attr("src",
                                        mobileui_ref.ui.def_cover);
                        };
                        mobileui_ref.rpc.send("web.writecover",
                                [media.media_id], cover_callback);
                    }
                    else {
                        var str = mobileui_ref.getString("no-media",
                                "No Playing Media");
                        $("#playing-title").html(str);
                        $("#playing-cover").attr("src",
                                mobileui_ref.ui.def_cover);
                    }

                };
                mobileui_ref.rpc.send("player.current", [], current_callback);
            }
            else {
                var str = mobileui_ref.getString("no-media","No Playing Media");
                $("#playing-title").html(str);
                $("#playing-cover").attr("src", mobileui_ref.ui.def_cover);
            }

            this._current = current;
        }
    },

};

//
// Current Mode Page
//
var _ModePage = function(st) {
    this.pager_support = true;
};
_ModePage.prototype =
{
    initialize: function(st, controller) {
        this._pager = null;
        this._id = -1;
        this._controller = controller;
        // vars for pager
        this.current_page = null;
        this.current_length = null;
        this.total_page = null;

        // set title
        $("#mode-title").html(this.title);

        // build toolbar
        this.buildToolbar();
        // update options
        if (this.has_options) {
            $("#playorder-option").val(st[st.mode+"playorder"]);
            var ck = st[st.mode+"repeat"] == "1" ? true : false;
            $("#repeat-option").attr("checked", ck);
        }
        this.update(st);
        $("#current_mode_page").show();
    },

    closeExtra: function() {
        $('#mode-extra').hide();
        $('#mode-main').show();

        // update media info width
        var mode = mobileui_ref.ui.getCurrentMode();
        var win_width = $("#current_mode_page").width();
        var width = mode.has_selection ? win_width-85 : win_width-55;
        $(".media-info").css("width", width);
    },

    update: function(st) {
        if (parseInt(st[this._mode]) != this._id) {
            //update medialist
            this.updateMedialist(parseInt(st[this._mode+"length"]));
            this._id = parseInt(st[this._mode]);
        }
    },

    updateMedialist: function(length, page) {
        var callback = function(data) {
            var mode = mobileui_ref.ui.getCurrentMode();
            if (!mode) { return; } // page has change

            // first remove loading information
            $("#mode-content-list").empty();

            // build new medialist
            for (i in data.medias) {
                var infos = data.medias[i];
                var media = createElement("div", "media-item", {});

                if (mode.has_selection) {
                    var select = createElement("div", "media-select", {});
                    var input = document.createElement("input");
                    $(input).val(infos.id).attr("type","checkbox");
                    $(select).append(input);

                    $(media).append(select);
                }
                else {
                    // set left padding
                    $(media).css("padding-left", "10px");
                }

                var media_info = createElement("div", "media-info", {});
                var media_title = createElement("div", "media-title", {});
                var media_desc = createElement("div", "media-desc", {});
                if (infos.length)
                    var title = infos.title + " ("+
                        formatTime(infos.length)+")";
                else
                    var title = infos.title;
                switch (data.media_type) {
                    case "song":
                        var desc = infos.artist + " - " + infos.album;
                        break;
                    case "video":
                        var desc = infos.videoheight+" X "+infos.videowidth;
                        break;
                    case "webradio":
                        var desc = infos.url;
                        break;
                    case "dvd_track":
                        var desc = '';
                        break;
                }
                $(media_title).html(title);
                $(media_desc).html(desc);
                $(media_info).append(media_title);
                $(media_info).append(media_desc);
                $(media).append(media_info);

                var button = createElement("div", "media-play-btn",
                        {value: infos.id});
                $(button).click(function(evt) {
                    var id = $(evt.target).attr("value");
                    mobileui_ref.rpc.goto(id);
                    });
                $(media).append(button);

                $("#mode-content-list").append(media);
            }

            // set media info width
            var win_width = $("#current_mode_page").width();
            var width = mode.has_selection ? win_width-85 : win_width-55;
            $(".media-info").css("width", width);
        };

        // set pager
        $(".content-list-pager").hide();
        if (this.pager_support) {
            var NUMBER_PER_PAGE = 20;
            this.current_page = page ? parseInt(page) : 1;
            this.current_length = parseInt(length);
            this.total_page = parseInt(this.current_length/NUMBER_PER_PAGE)+1;
            if (this.total_page > 1) {
               $(".pager-desc").html(this.current_page+"/"+this.total_page);
               $(".content-list-pager").show();
            }
            var parms = [(this.current_page-1)*NUMBER_PER_PAGE,NUMBER_PER_PAGE];
        }
        else
            var parms = [];

        var loading = createElement("div", "list-loading", {});
        var str = mobileui_ref.getString("loading","Loading ...");
        $(loading).html(str);
        $("#mode-content-list").empty().append(loading);
        mobileui_ref.rpc.send(this._mode+".get", parms, callback)
    },

    buildToolbar: function() {
        var mode = this;
        var tb = this.toolbar;
        $("#mode-toolbar").empty();
        for (i in tb) {
            var button = document.createElement("div");
            if (typeof tb[i].cmd == "function")
                var func = tb[i].cmd;
            else
                var func = mode[tb[i].cmd];
            $(button).click(func).attr("id", tb[i].id).
                addClass("toolbar-button");
            $("#mode-toolbar").append(button);
        }
    },

    showOptions: function(evt) {
        $("#mode-extra-title").html("Options");
        $("#mode-main").hide();
        $("#mode-extra-content").hide();
        $("#mode-extra-options").show();
        $("#mode-extra").show();
    },

    setExtraLoading: function() {
        var loading = createElement("div", "list-loading", {});
        var str = mobileui_ref.getString("loading","Loading ...");
        $(loading).html(str);
        $("#mode-extra-content").empty().append(loading).show();
        $("#mode-main").hide();
        $("#mode-extra-options").hide();
        $("#mode-extra").show();
    },

    getSelection: function(mode) {
        if (mode.has_selection) {
            // get selected items
            var items = $(".media-select");
            var selections = new Array();
            for (var i = 0; item = items[i]; i++) {
                var input = item.getElementsByTagName("input").item(0);
                if (input.checked)
                    selections.push(input.value)
            }

            if (selections.length > 0) { // send rpc command
               return selections;
            }
        }
        return null;
    },
};

/*
 * Playlist
 */
function PlaylistMode(st) {
    this.has_options = true;
    this.has_selection = true;
    this.title = mobileui_ref.getString("pls-mode","Playlist Mode");
    this._mode = "playlist";
    this.toolbar = [
        {id: "pl-opt", cmd: "showOptions"},
        {id: "pl-add", cmd: "showLibrary"},
        {id: "pl-remove", cmd: "remove"},
        {id: "pl-shuffle", cmd: "shuffle"},
        {id: "pl-clear", cmd: "clear"},
    ];
    this.initialize(st);
    this.extra_pager = new Pager(function(evt, page) {
        var mode = mobileui_ref.ui.getCurrentMode();
        mode.showLibrary(evt, mode.current_dir, page);
    });

    return this;
};
PlaylistMode.prototype = new _ModePage;
PlaylistMode.prototype.showLibrary = function(evt, dir, page) {
    if (!page) { page = 1; }
    var mode = mobileui_ref.ui.getCurrentMode();
    mode.current_dir = dir;

    var callback = function(data) {
        var buildItem = function(title, value, type) {
            var item = createElement("div", "library-item", {});
            var select = createElement("div", "library-select", {});
            if (title != "..") {
                var input = document.createElement("input");
                $(input).val(value).attr("type","checkbox");
                $(select).append(input);
            }
            $(item).append(select);
            var title_div = createElement("div", type, {});
            $(title_div).html(title);
            $(item).append(title_div);

            if (type == "directory") {
                var button = createElement("div", "media-play-btn", {});
                $(button).attr("value", value);
                $(button).click(function(evt) {
                    var dir = $(evt.target).attr("value");
                    var mode = mobileui_ref.ui.getCurrentMode();
                    if (mode)
                        mode.showLibrary(evt, dir);
                    });
                $(item).append(button);
            }
            return item;
        };

        $("#mode-extra-content").empty();
        var mode = mobileui_ref.ui.getCurrentMode();

        // pager
        mode.extra_pager.update(data.directories.length+data.files.length,page);
        var items = data.directories.concat(data.files);
        var extract = items.slice(
                mode.extra_pager.NUMBER_PER_PAGE*(parseInt(page)-1),
                mode.extra_pager.NUMBER_PER_PAGE*(parseInt(page)));


        if (data.root != '') {
            var idx = data.root.lastIndexOf("/");
            var root = data.root.substring(0, idx);
            $("#mode-extra-content").append(buildItem("..", root, "directory"));
        }
        // files and directories
        for (var i=0; item=extract[i]; i++) {
            if (typeof(item) == "object") { // it is a file
                var value = item.filename;
                var type = "file";
            }
            else {// it is a folder
                var value = item;
                var type = "directory";
            }

            var path = data.root != '' ? data.root + "/" + value : value;
            $("#mode-extra-content").append(buildItem(value, path, type));
        }

        // pager
        if (mode.extra_pager.total_page > 1) {
            $("#mode-extra-content").prepend(mode.extra_pager.build());
            $("#mode-extra-content").append(mode.extra_pager.build());
        }

        // submit button
        var str = mobileui_ref.getString("load-files","Load Files");
        var button = createElement("div", "center", {});
        var input = createElement("input", "form-submit",
                {type: "submit", value: str});
        $(input).click(function(evt) {
            //get selections
            var items = $(".library-select");
            var selections = new Array();
            for (var i = 0; item = items[i]; i++) {
                var input = item.getElementsByTagName("input").item(0);
                if (input && input.checked)
                    selections.push(input.value)
            }

            if (selections.length > 0) { // send rpc command
                mobileui_ref.rpc.plsModeAddPath(selections);
            }
        });
        $(button).append(input);
        $("#mode-extra-content").append(button);

        $(".file").css("width", $("#mode-extra-content").width() - 45);
        $(".directory").css("width", $("#mode-extra-content").width() - 85);
    };

    var str = mobileui_ref.getString("audio-library","Audio Library");
    $("#mode-extra-title").html(str);
    mode.setExtraLoading();

    var parms = [];
    if (dir) { parms.push(dir); }
    mobileui_ref.rpc.send("audiolib.getDir", parms, callback);
};
PlaylistMode.prototype.shuffle = function(evt) {
    mobileui_ref.rpc.plsModeShuffle();
};
PlaylistMode.prototype.clear = function(evt) {
    mobileui_ref.rpc.plsModeClear();
};
PlaylistMode.prototype.remove = function(evt) {
    var mode = mobileui_ref.ui.getCurrentMode();
    var selections = mode.getSelection(mode);
    if (selections) { // send rpc command
        mobileui_ref.rpc.plsModeRemove(selections);
    }
};

/*
 * Video
 */
function VideoMode(st) {
    this.has_options = true;
    this.has_selection = false;
    this.title = mobileui_ref.getString("video-mode","Video Mode")
    this._mode = "video";
    this.toolbar = [
        {id: "video-opt", cmd: "showOptions"},
        {id: "video-set", cmd: "showLibrary"},
        {id: "video-search", cmd: "search"},
    ];
    this.initialize(st);
    this.extra_pager = new Pager(function(evt, page) {
        var mode = mobileui_ref.ui.getCurrentMode();
        mode.showLibrary(evt, mode.current_dir, page);
    });

    return this;
};
VideoMode.prototype = new _ModePage;
VideoMode.prototype.showLibrary = function(evt, dir, page) {
    if (!page) { page = 1; }
    var mode = mobileui_ref.ui.getCurrentMode();
    mode.current_dir = dir;

    var callback = function(data) {
        var buildItem = function(title, value) {
            var item = createElement("div", "library-item", {});
            var select = createElement("div", "library-apply", {});
            if (title != "..") {
                var input = createElement("div", "apply-btn", {value: value});
                $(input).click(function(evt) {
                    var dir = $(evt.target).attr("value");
                    mobileui_ref.rpc.videoSet(dir, "directory");
                    $("#mode-extra").hide();
                    $("#mode-main").show();
                    });
                $(select).append(input);
            }

            $(item).append(select);
            var title_div = createElement("div", "directory", {});
            $(title_div).html(title);
            $(item).append(title_div);

            var button = createElement("div", "media-play-btn", {value: value});
            $(button).click(function(evt) {
                var dir = $(evt.target).attr("value");
                var mode = mobileui_ref.ui.getCurrentMode();
                if (mode)
                    mode.showLibrary(evt, dir);
                });
            $(item).append(button);
            return item;
        };

        $("#mode-extra-content").empty();
        var mode = mobileui_ref.ui.getCurrentMode();

        if (data.root != '') {
            var idx = data.root.lastIndexOf("/");
            var root = data.root.substring(0, idx);
            $("#mode-extra-content").append(buildItem("..", root));
        }
        // directories
        mode.extra_pager.update(data.directories.length, page);
        var extract = data.directories.slice(
                mode.extra_pager.NUMBER_PER_PAGE*(parseInt(page)-1),
                mode.extra_pager.NUMBER_PER_PAGE*(parseInt(page)));
        for (var i=0; dir=extract[i]; i++) {
            var path = dir;
            if (data.root != '')
                path = data.root + "/" + path;
            $("#mode-extra-content").append(buildItem(dir, path));
        }
        $(".directory").css("width", $("#mode-extra-content").width() - 85);

        // pager
        if (mode.extra_pager.total_page > 1) {
            $("#mode-extra-content").prepend(mode.extra_pager.build());
            $("#mode-extra-content").append(mode.extra_pager.build());
        }
    };

    var str = mobileui_ref.getString("video-library","Video Library");
    $("#mode-extra-title").html(str);
    mode.setExtraLoading();

    var parms = [];
    if (dir) { parms.push(dir); }
    mobileui_ref.rpc.send("videolib.getDir", parms, callback);
};
VideoMode.prototype.search = function(evt) {
    var box = createElement("div", "center", {});
    var input = createElement("input", "form-text",
            {id: "search-input", type: "text", size: 36, maxlength: 64});
    var submit = createElement("input", "form-input",
        {value: mobileui_ref.getString("search","Search"), type: "submit"});
    $(submit).click(function(evt) {
        var value = $("#search-input").val();
        if (value != '') {
            mobileui_ref.rpc.videoSet(value, "search");
            $("#mode-extra").hide();
            $("#mode-main").show();
        }
        return false;
    });

    $(box).append(input).append(submit);
    $("#mode-extra-title").html(mobileui_ref.getString("search","Search"));
    $("#mode-extra-content").empty().append(box).show();
    $("#mode-extra-options").hide();
    $("#mode-main").hide();
    $("#mode-extra").show();
    return false;
};

/*
 * Webradio
 */
function WebradioMode(st) {
    this.has_options = false;
    this.has_selection = true;
    this.title = mobileui_ref.getString("wb-mode","Webradio Mode")
    this._mode = "webradio";
    this.toolbar = [
        {id: "wb-add", cmd: "add"},
        {id: "wb-remove", cmd: "remove"},
        {id: "wb-clear", cmd: "clear"},
    ];
    this.initialize(st);

    return this;
};
WebradioMode.prototype = new _ModePage;
WebradioMode.prototype.clear = function(evt) {
    mobileui_ref.rpc.wbModeClear();
};
WebradioMode.prototype.remove = function(evt) {
    var mode = mobileui_ref.ui.getCurrentMode();
    var selections = mode.getSelection(mode);
    if (selections) { // send rpc command
        mobileui_ref.rpc.wbModeRemove(selections);
    }
};
WebradioMode.prototype.add = function(evt) {
    var name_box = createElement("div", "wb-input", {});
    var title = document.createElement("span");
    $(title).html(mobileui_ref.getString("wb-name","Webradio Name"));
    var input = createElement("input", "form-text",
           {id: "wb-name", type:"text", size: 24, maxlength: 64});
    $(name_box).append(title).append(input);

    var url_box = createElement("div", "wb-input", {});
    var title = document.createElement("span");
    $(title).html(mobileui_ref.getString("wb-url","Webradio URL"));
    var input = createElement("input", "form-text",
           {id: "wb-url", type:"text", size: 24, maxlength: 128});
    $(name_box).append(title).append(input);

    var button = createElement("div", "center", {});
    var input = createElement("input", "form-submit",
           {value: mobileui_ref.getString("add", "Add"), type:"submit"});
    $(input).click(function(evt) {
        var name = $("#wb-name").val();
        var url = $("#wb-url").val();
        if (name != "" && url != "") {
            mobileui_ref.rpc.wbModeAdd(name, url);
            $("#mode-extra").hide();
            $("#mode-main").show();
        }
    });
    $(button).append(input);

    $("#mode-extra-options").hide();
    $("#mode-extra-title").html(
            mobileui_ref.getString("wb-add","Add a Webradio"));
    $("#mode-extra-content").empty().append(name_box).append(url_box)
                            .append(button).show();
    $("#mode-main").hide();
    $("#mode-extra").show();
    return false;
};

/*
 * dvd
 */
function DvdMode(st) {
    this.has_options = false;
    this.pager_support = false;
    this.has_selection = false;
    this.title = mobileui_ref.getString("dvd-mode","DVD Mode")
    this._mode = "dvd";
    this.toolbar = [
        {id: "dvd-load", cmd: "reload"},
    ];
    this.initialize(st);

    return this;
};
DvdMode.prototype = new _ModePage;
DvdMode.prototype.reload = function(evt) { mobileui_ref.rpc.dvdModeReload(); };

/*
 * Panel
 */
function PanelMode(st) {
    this.has_options = true;
    this.has_selection = false;
    this.title = mobileui_ref.getString("panel-mode","Panel Mode")
    this._mode = "panel";
    this.toolbar = [
        {id: "panel-opt", cmd: "showOptions"},
        {id: "panel-set", cmd: "showTags"},
    ];
    this.initialize(st);

    // init var to update panel filter
    this.filters = null;
    this.current_tag = null;
    // get tag list
    this.tags = null;
    var taglist_callback = function(data) {
        var mode = mobileui_ref.ui.getCurrentMode();
        mode.tags = data;
    };
    mobileui_ref.rpc.send("panel.tags", [], taglist_callback);

    return this;
};
PanelMode.prototype = new _ModePage;
PanelMode.prototype.showTags = function(evt, tag_pos) {
    var mode = mobileui_ref.ui.getCurrentMode();
    var tag = tag_pos ? mode.tags[tag_pos] : mode.tags[0];
    if (tag) {
        mode.current_tag = tag;
        if (tag == mode.tags[0]) { // init filters
            mode.filters = {type: "complex", id: "and", value: []};
        }

        var callback = function(data) {
            $("#mode-extra-content").empty();
            // add a item to select all
            data.unshift("__all__");

            // build list
            for (idx in data) {
                var item = createElement("div", "tag-item", {});
                var text = data[idx];
                if (text == "__all__")
                    text = mobileui_ref.getString("all","All");
                else if (text == "__various__")
                    text = mobileui_ref.getString("various","Varioust Artist");
                else if (text == "")
                    text = mobileui_ref.getString("unknown","Unknown");
                $(item).attr("value", data[idx]).html(text).click(function(evt){
                    var mode = mobileui_ref.ui.getCurrentMode();
                    var pattern = $(evt.target).attr("value");
                    // update filters
                    if (pattern != "__all__") {
                        var n_filter = {type: "basic", id: "equals",
                          value: {tag: mode.current_tag, pattern: pattern}};
                        mode.filters.value.push(n_filter);
                    }


                    var n_idx = 1+mode.tags.indexOf(mode.current_tag);
                    if (n_idx < mode.tags.length)
                        mode.showTags(evt, n_idx);
                    else {
                        var null_callback = function(data) {};
                        mobileui_ref.rpc.pnModeClearFilter();
                        mobileui_ref.rpc.pnModeClearSearch();
                        for (i in mode.filters.value) {
                            var f = mode.filters.value[i];
                            mobileui_ref.rpc.send("panel.setFilter",
                              [f.value.tag, [f.value.pattern]], null_callback);
                        }
                        mobileui_ref.rpc.pnModeSetActiveList("panel", "");
                        $("#mode-extra").hide();
                        $("#mode-main").show();
                    }
                });

                $("#mode-extra-content").append(item);
            }
        };

        $("#mode-extra-title").html(mobileui_ref.getString(tag, tag));
        mode.setExtraLoading();
        mobileui_ref.rpc.send("audiolib.taglist", [tag,mode.filters], callback);
    }
};

// vim: ts=4 sw=4 expandtab
