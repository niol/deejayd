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

import org.mroy31.deejayd.common.events.StatusChangeEvent;
import org.mroy31.deejayd.common.events.StatusChangeHandler;
import org.mroy31.deejayd.mobile.sources.DeejaydMode;
import org.mroy31.deejayd.mobile.sources.DvdMode;
import org.mroy31.deejayd.mobile.sources.PanelMode;
import org.mroy31.deejayd.mobile.sources.PlaylistMode;
import org.mroy31.deejayd.mobile.sources.VideoMode;
import org.mroy31.deejayd.mobile.sources.WebradioMode;
import org.mroy31.deejayd.mobile.widgets.WallToWallPanel;

public class SourcePanel extends WallToWallPanel implements StatusChangeHandler{
    private String currentMode = "";
    private DeejaydMode current = null;

    public SourcePanel(WallToWallPanel parent) {
        super("", parent);

        ui.addStatusChangeHandler(this);
    }

    @Override
    protected String getShortTitle() {
        return "Mode";
    }

    @Override
    public void onStatusChange(StatusChangeEvent event) {
        String mode = event.getStatus().get("mode");
        if (!mode.equals(currentMode)) {
            clear();
            current = getMode(mode);
            add(current);
            setWallTitle(current.getTitle());

            current.onStatusChange(event);
            currentMode = mode;
        }
    }

    private DeejaydMode getMode(String name) {
        if (name.equals("playlist")) {
            return new PlaylistMode();
        } else if (name.equals("webradio")) {
            return new WebradioMode();
        } else if (name.equals("video")) {
            return new VideoMode();
        } else if (name.equals("panel")) {
            return new PanelMode();
        } else if (name.equals("dvd")) {
            return new DvdMode();
        }
        return null;
    }
}

//vim: ts=4 sw=4 expandtab