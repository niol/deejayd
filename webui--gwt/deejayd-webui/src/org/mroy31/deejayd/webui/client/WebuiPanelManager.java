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

public class WebuiPanelManager extends Composite
        implements StatusChangeHandler {

    class ModeException extends Exception {
        private static final long serialVersionUID = 1L;
    }
    private static WebuiPanelManagerUiBinder uiBinder = GWT
            .create(WebuiPanelManagerUiBinder.class);

    interface WebuiPanelManagerUiBinder extends
            UiBinder<Widget, WebuiPanelManager> {
    }

    @UiField DeckPanel deckPanel;
    @UiField(provided = true) final WebuiResources resources;

    private WebuiLayout ui;
    private WebuiPanel currentPanel;

    public WebuiPanelManager(WebuiLayout webui) {
        this.resources = webui.resources;
        this.ui = webui;

        initWidget(uiBinder.createAndBindUi(this));
        this.ui.addStatusChangeHandler(this);
    }

    private class ModeAsyncCallback implements RunAsyncCallback {
        private StatusChangeEvent event;

        public ModeAsyncCallback(StatusChangeEvent event) {
            this.event = event;
        }

        @Override
        public void onFailure(Throwable reason) {
            ui.setError("Unable to load mode");
        }

        @Override
        public void onSuccess() {
            HashMap<String, String> status = event.getStatus();
            if (currentPanel == null
                    || !currentPanel.getSourceName().equals(status.get("mode"))) {
                deckPanel.showWidget(0);
                if (currentPanel != null)
                    currentPanel.removeFromParent();

                try {
                    currentPanel = getPanel(status.get("mode"));
                } catch (ModeException ex) {
                    ui.setError("Unable to init current mode");
                    return;

                }
                deckPanel.add(currentPanel);
                deckPanel.showWidget(1);

                if (currentPanel instanceof StatusChangeHandler) {
                    StatusChangeHandler p = (StatusChangeHandler) currentPanel;
                    p.onStatusChange(event);
                }
            }
        }

        private WebuiPanel getPanel(String sourceName) throws ModeException {
            if (sourceName.equals("playlist")) {
                return new PlaylistPanel(ui);
            } else if (sourceName.equals("webradio")) {
                return new WebradioPanel(ui);
            } else if (sourceName.equals("panel")) {
                return new NavigationPanel(ui);
            }
            throw new ModeException();
        }
    }

    public void onStatusChange(StatusChangeEvent event) {
        GWT.runAsync(new ModeAsyncCallback(event));
    }

    public WebuiPanel getCurrentPanel() {
        return currentPanel;
    }
}

//vim: ts=4 sw=4 expandtab