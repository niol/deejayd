/*
 * Deejayd, a media player daemon
 * Copyright (C) 2007-2009 Mickael Royer <mickael.royer@gmail.com>
 *                         Alexandre Rossi <alexandre.rossi@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
 */

package org.mroy31.deejayd.mobile.client;

import java.util.HashMap;

import org.mroy31.deejayd.common.events.StatusChangeEvent;
import org.mroy31.deejayd.common.events.StatusChangeHandler;
import org.mroy31.deejayd.mobile.widgets.WallToWallPanel;

import com.google.gwt.user.client.Command;

public class PlayerPanel extends WallToWallPanel implements StatusChangeHandler{
    private String current = "";
    private String state = "";
    private int volume = -1;

    private PlayerUI player = new PlayerUI(new PlayerUI.MediaChangeHandler() {
        public void onMediaChange(String title) {
            setWallTitle(title, true);
        }
    });

    public PlayerPanel(WallToWallPanel parent) {
        super("", parent);

        add(player);
        ui.addStatusChangeHandler(this);
        setWallTitle(ui.i18nConst.noPlayingMedia());

        // set refresh button
        setRightCommand(ui.i18nConst.refresh(), "refresh", new Command() {
            public void execute() {
                ui.update();
            }
        });
    }

    @Override
    protected String getShortTitle() {
        return ui.i18nConst.player();
    }

    public void onStatusChange(StatusChangeEvent event) {
        HashMap<String, String> status = event.getStatus();
        // update state
        if (!status.get("state").equals(state)) {
            state = status.get("state");
            player.updateState(state);
        }

        // update volume
        int vol = Integer.parseInt(status.get("volume"));
        if (vol != volume) {
            player.updateVolume(vol);
            volume = vol;
        }

        // update current media
        if (!state.equals("stop")) {
            String[] times = status.get("time").split(":");
            if (!status.get("current").equals(this.current)) {
                player.updateCurrent();
                current = status.get("current");
                player.seekBar.setMaxValue(Integer.parseInt(times[1]));
            }
            player.seekBar.setValue(Integer.parseInt(times[0]), false);
        } else if (!current.equals("")) {
            player.resetCover();
            setWallTitle(ui.i18nConst.noPlayingMedia());
            current = "";
        }
    }
}

//vim: ts=4 sw=4 expandtab