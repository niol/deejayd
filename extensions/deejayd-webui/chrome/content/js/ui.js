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

function UI(controller)
{
    this.modes = {}; this.libraries = {}; this.panels = {};
    this.__current_mode = null;
    this.modes_sel = {
        playlist: 0,
        panel: 1,
        webradio: 2,
        video: 3,
        dvd: 4,
    };

    this.initialize(controller);
    return this;
}

UI.prototype =
{
    initialize: function(controller) {
        xului_ref.rpc.onrequeststart = function(){
            $("msg-loading").style.display = 'block';
        };
        xului_ref.rpc.onrequeststop = function(){
            $("msg-loading").style.display = 'none';
        };

        // init player
        this.player = new Player();
        // recorded playlist
        this.rec_pls = new RecordedPlaylist();
        // queue
        this.queue = new Queue(this.rec_pls);

        // init modes and libraries
        var ui = this;
        var callback = function(data) {
            // Build audio library
            ui.libraries.audio = new AudioLibrary();
            for (idx in data) {
                if (data[idx] == "1") {
                    switch (idx) {
                        case "playlist":
                            ui.panels.playlist = new PlsModePanel(
                                    ui.libraries.audio, ui.rec_pls);
                            ui.modes.playlist = new PlaylistMode(
                                    ui.panels.playlist, ui.rec_pls);
                        break;
                        case "panel":
                            ui.panels.panel = new PanelModePanel(
                                    ui.libraries.audio, ui.rec_pls);
                            ui.modes.panel = new PanelMode(ui.rec_pls);
                        break;
                        case "webradio":
                            ui.modes.wb = new WebradioMode();
                        break;
                        case "video":
                            ui.libraries.video = new VideoLibrary();
                            ui.panels.video = new VideoModePanel(
                                    ui.libraries.video);
                            ui.modes.video = new VideoMode(ui.panels.video);
                        break;
                        case "dvd":
                            ui.modes.dvd = new DvdMode();
                        break;
                    }
                }
            }
            // init queue
        };
        controller.rpc.send("availablemodes", [], callback);
    },

    getMode: function(mode) {
        return xului_ref.ui.modes[mode] ? xului_ref.ui.modes[mode] : null;
    },

    updateMode: function() {
        xului_ref.rpc.setMode($("mode-menu").value);
    },

    updateStatus: function(st) {
        if (st.mode != xului_ref.ui.current_mode) {
            $('main').selectedIndex = xului_ref.ui.modes_sel[st.mode];
            $('mode-menu').value = st.mode;

            xului_ref.ui.current_mode = st.mode;
        }

        // update player
        xului_ref.ui.player.update(st);
        // update queue
        xului_ref.ui.queue.update(st);
        // update modes
        for (idx in xului_ref.ui.modes)
            xului_ref.ui.modes[idx].update(st);
    },

    updateStats: function(stats) {
        for (idx in xului_ref.ui.libraries) {
            xului_ref.ui.libraries[idx].update(stats);
        }
    },

    setRating: function(mode, rating) {
        if (mode != "queue")
            var selections = this.modes[mode].getSelection("value");
        else
            var selections = this.queue.getSelection("value");
        xului_ref.rpc.setMediaRating(selections, rating);
    },

};

// vim: ts=4 sw=4 expandtab
