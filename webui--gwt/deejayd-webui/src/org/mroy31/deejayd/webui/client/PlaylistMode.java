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

import org.mroy31.deejayd.common.rpc.DefaultRpcCallback;
import org.mroy31.deejayd.common.widgets.DeejaydUIWidget;
import org.mroy31.deejayd.common.widgets.DeejaydUtils;
import org.mroy31.deejayd.webui.medialist.SongRenderer;
import org.mroy31.deejayd.webui.widgets.NewPlsDialog;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.Widget;

public class PlaylistMode extends DefaultWebuiMode implements ClickHandler {

    private Label description;
    private Button plsShuffle;
    private Button plsClear;
    private Button plsRemove;
    private Button goToCurrent;
    private Button plsSave;

    private class PlsCallback extends DefaultRpcCallback {
        public PlsCallback(DeejaydUIWidget ui) { super(ui); }

        @Override
        public void onCorrectAnswer(JSONValue data) {
            WebuiLayout layout = (WebuiLayout) ui;
            PlaylistPanel p = (PlaylistPanel)
                    layout.panelManager.getCurrentPanel();
            p.buildPlsList();

            layout.setMessage(layout.i18nConstants.plsSaveMsg());
        }
    }
    private NewPlsDialog saveDg;

    public PlaylistMode(WebuiLayout webui) {
        super("playlist", webui, true, true);
        saveDg = new NewPlsDialog(new NewPlsDialog.PlsCommand() {
            @Override
            public void execute(String plsName) {
                ui.rpc.plsModeSave(plsName, new PlsCallback(ui));
            }
        });
        mediaList.setOption(true, new SongRenderer(ui, "playlist", loadLabel));
    }

    void buildTopToolbar(HorizontalPanel toolbar) {
        HorizontalPanel optionPanel = new HorizontalPanel();
        optionPanel.add(makePlayorderWidget());
        optionPanel.add(makeRepeatWidget());
        toolbar.add(optionPanel);

        description = new Label();
        description.addStyleName(resources.webuiCss().toolbarDescLabel());
        toolbar.setHorizontalAlignment(HorizontalPanel.ALIGN_RIGHT);
        toolbar.add(description);
    }

    public void buildBottomToolbar(HorizontalPanel toolbar) {
        if (plsShuffle == null) {
            plsShuffle = new Button(ui.i18nConstants.shuffle());
            plsShuffle.setStyleName(
                    ui.resources.webuiCss().modeToolbarButton() + " " +
                    ui.resources.webuiCss().shuffleButton());
            plsShuffle.addClickHandler(this);
        }
        toolbar.add(plsShuffle);

        if (plsClear == null) {
            plsClear = new Button(ui.i18nConstants.clear());
            plsClear.setStyleName(
                    ui.resources.webuiCss().modeToolbarButton() + " " +
                    ui.resources.webuiCss().clearButton());
            plsClear.addClickHandler(this);
        }
        toolbar.add(plsClear);

        if (plsRemove == null) {
            plsRemove = new Button(ui.i18nConstants.remove());
            plsRemove.setStyleName(
                    ui.resources.webuiCss().modeToolbarButton() + " " +
                    ui.resources.webuiCss().removeButton());
            plsRemove.addClickHandler(this);
        }
        toolbar.add(plsRemove);

        if (plsSave == null) {
            plsSave = new Button(ui.i18nConstants.save());
            plsSave.setStyleName(
                    ui.resources.webuiCss().modeToolbarButton() + " " +
                    ui.resources.webuiCss().saveButton());
            plsSave.addClickHandler(this);
        }
        toolbar.add(plsSave);

        if (goToCurrent == null) {
            goToCurrent = new Button(ui.i18nConstants.goCurrentSong());
            goToCurrent.setStyleName(
                    ui.resources.webuiCss().modeToolbarButton() + " " +
                    ui.resources.webuiCss().gotoButton());
            goToCurrent.addClickHandler(this);
        }
        toolbar.add(goToCurrent);
    }

    protected void setDescription(int length, int timelength) {
        if (description != null) {
            if (length == 0) {
                description.setText(ui.i18nMessages.songsDesc(length));
            } else {
                String timeDesc = DeejaydUtils.formatTimeLong(timelength,
                        ui.i18nMessages);
                description.setText(ui.i18nMessages.songsDesc(length)+" ("+
                        timeDesc+")");
            }
        }
    }

    public void onClick(ClickEvent event) {
        Widget sender = (Widget) event.getSource();
        if (sender == plsShuffle) {
            ui.rpc.plsModeShuffle(new DefaultRpcCallback(ui));
        } else if (sender == plsClear) {
            ui.rpc.plsModeClear(new DefaultRpcCallback(ui));
        } else if (sender == plsRemove) {
            ui.rpc.plsModeRemove(mediaList.getSelection(),
                    new DefaultRpcCallback(ui));
        } else if (sender == goToCurrent) {
            if (currentPlayingPos != -1) {
                mediaList.goTo(currentPlayingPos);
            }
        } else if (sender == plsSave) {
            saveDg.center();
        }
    }
}

//vim: ts=4 sw=4 expandtab