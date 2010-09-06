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

import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.common.widgets.DeejaydUtils;
import org.mroy31.deejayd.webui.events.DragLeaveEvent;
import org.mroy31.deejayd.webui.events.DragOverEvent;
import org.mroy31.deejayd.webui.events.DropEvent;
import org.mroy31.deejayd.webui.medialist.MediaListDropCommand;
import org.mroy31.deejayd.webui.medialist.SongRenderer;
import org.mroy31.deejayd.webui.widgets.NewPlsDialog;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
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

    private int currentOverRow = -1;
    private NewPlsDialog saveDg;

    public PlaylistMode(WebuiLayout webui) {
        super("playlist", webui, true, true);
        saveDg = new NewPlsDialog(new NewPlsDialog.PlsCommand() {
            public void execute(String plsName) {
                ui.rpc.plsModeSave(plsName, new AnswerHandler<Boolean>() {

                    public void onAnswer(Boolean answer) {
                        PlaylistPanel p = (PlaylistPanel)
                                ui.panelManager.getCurrentPanel();
                        p.buildPlsList();

                        ui.setMessage(ui.i18nConstants.plsSaveMsg());
                    }
                });
            }
        });
        mediaList.setOption(true, new SongRenderer(ui, "playlist", loadLabel));
        mediaList.addDragDropCommand(new MediaListDropCommand() {

            public void onDrop(DropEvent event, int row) {
                String[] data = event.dataTransfert().getData().split("-");
                if (data[0].equals("playlist")) {
                    ui.rpc.plsModeMove(new String[] {data[1]}, row, null);
                    if (currentOverRow != -1) {
                        mediaList.getRowFormatter().removeStyleName(
                                currentOverRow,
                                ui.resources.webuiCss().mlRowOver());
                        currentOverRow = -1;
                    }
                }
            }

            public void onDragOver(DragOverEvent event, int row) {
                String[] data = event.dataTransfert().getData().split("-");
                if (data[0].equals("playlist")) {
                    if (row != currentOverRow) {
                        if (currentOverRow != -1) {
                            mediaList.getRowFormatter().removeStyleName(
                                currentOverRow,
                                ui.resources.webuiCss().mlRowOver());
                        }
                        if (row != -1 )
                            mediaList.getRowFormatter().addStyleName(row,
                                    ui.resources.webuiCss().mlRowOver());
                        currentOverRow = row;
                    }
                }
            }

            public void onDragLeave(DragLeaveEvent event) {
                if (currentOverRow != -1) {
                    mediaList.getRowFormatter().removeStyleName(
                        currentOverRow, ui.resources.webuiCss().mlRowOver());
                    currentOverRow = -1;
                }
            }
        });
    }

    @Override
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

    @Override
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

    @Override
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
            ui.rpc.plsModeShuffle();
        } else if (sender == plsClear) {
            ui.rpc.plsModeClear();
        } else if (sender == plsRemove) {
            ui.rpc.plsModeRemove(mediaList.getSelection(), null);
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