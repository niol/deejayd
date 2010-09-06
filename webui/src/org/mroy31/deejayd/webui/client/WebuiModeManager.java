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

package org.mroy31.deejayd.webui.client;

import java.util.HashMap;

import org.mroy31.deejayd.common.events.StatusChangeEvent;
import org.mroy31.deejayd.common.events.StatusChangeHandler;
import org.mroy31.deejayd.webui.resources.WebuiResources;

import com.google.gwt.core.client.GWT;
import com.google.gwt.core.client.RunAsyncCallback;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.DeckPanel;
import com.google.gwt.user.client.ui.Widget;

public class WebuiModeManager extends Composite implements StatusChangeHandler {

    class ModeException extends Exception {
        private static final long serialVersionUID = 1L;
    }
    private static WebuiModeManagerUiBinder uiBinder = GWT
            .create(WebuiModeManagerUiBinder.class);
    interface WebuiModeManagerUiBinder extends
            UiBinder<Widget, WebuiModeManager> {
    }

    @UiField DeckPanel deckPanel;
    @UiField(provided = true) final WebuiResources resources;

    private WebuiLayout ui;
    private WebuiModeInterface currentMode;

    public WebuiModeManager(WebuiLayout ui) {
        this.resources = ui.resources;
        this.ui = ui;

        initWidget(uiBinder.createAndBindUi(this));
        deckPanel.showWidget(0);
        this.ui.addStatusChangeHandler(this);
    }

    private class ModeAsyncCallback implements RunAsyncCallback {
        private HashMap<String, String> status;

        public ModeAsyncCallback(HashMap<String, String> status) {
            this.status = status;
        }

        public void onFailure(Throwable reason) {
            ui.setMessage("Unable to load mode", "error");
        }

        public void onSuccess() {
            if (currentMode == null
                    || !currentMode.getSourceName().equals(status.get("mode"))) {
                deckPanel.showWidget(0);
                if (currentMode != null)
                    currentMode.removeFromParent();

                try {
                    currentMode = getMode(status.get("mode"));
                } catch (ModeException ex) {
                    ui.setMessage("Unable to init current mode", "error");
                    return;

                }
                deckPanel.add((Widget) currentMode);
                deckPanel.showWidget(1);
            }
            currentMode.onStatusChange(status);
        }

        private WebuiModeInterface getMode(String sourceName)
                throws ModeException {
            if (sourceName.equals("playlist")) {
                return new PlaylistMode(ui);
            } else if (sourceName.equals("webradio")) {
                return new WebradioMode(ui);
            } else if (sourceName.equals("panel")) {
                return new NavigationPanelMode(ui);
            } else if (sourceName.equals("video")) {
                return new VideoMode(ui);
            } else if (sourceName.equals("dvd")) {
                return new DvdMode(ui);
            }
            throw new ModeException();
        }
    }

    public void onStatusChange(StatusChangeEvent event) {
        HashMap<String, String> status = event.getStatus();
        GWT.runAsync(new ModeAsyncCallback(status));
    }
}

//vim: ts=4 sw=4 expandtab