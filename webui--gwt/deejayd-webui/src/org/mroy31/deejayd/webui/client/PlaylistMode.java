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
import org.mroy31.deejayd.common.rpc.GenericRpcCallback;
import org.mroy31.deejayd.common.widgets.DeejaydUtils;
import org.mroy31.deejayd.common.widgets.IsLayoutWidget;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.DialogBox;
import com.google.gwt.user.client.ui.FlexTable;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.google.gwt.user.client.ui.Widget;

public class PlaylistMode extends WebuiMode implements ClickHandler {

    private Label description;
    private Button plsShuffle;
    private Button plsClear;
    private Button plsRemove;
    private Button goToCurrent;
    private Button plsSave;

    private static class SaveDialog extends DialogBox {
        private WebuiLayout ui;
        private TextBox input;
        private class PlsCallback extends GenericRpcCallback {
            public PlsCallback(IsLayoutWidget ui) { super(ui); }

            @Override
            public void onCorrectAnswer(JSONValue data) {
                WebuiLayout layout = (WebuiLayout) ui;
                PlaylistPanel p = (PlaylistPanel)
                        layout.panelManager.getCurrentPanel();
                p.buildPlsList();

                layout.setMessage(layout.i18nConstants.plsSaveMsg());
            }
        }

        public SaveDialog(WebuiLayout webui) {
            ui = webui;
            // Set the dialog box's caption.
            setText(ui.i18nConstants.saveDgCaption());
            // Enable animation.
            setAnimationEnabled(true);
            // Enable glass background.
            setGlassEnabled(true);

            VerticalPanel panel = new VerticalPanel();
            panel.setSpacing(2);
            HorizontalPanel buttonPanel = new HorizontalPanel();
            buttonPanel.setSpacing(3);

            input = new TextBox();
            panel.add(input);

            Button cancel = new Button(ui.i18nConstants.cancel());
            cancel.addClickHandler(new ClickHandler() {
                public void onClick(ClickEvent event) {
                    SaveDialog.this.hide();
                }
            });
            buttonPanel.add(cancel);
            Button save = new Button(ui.i18nConstants.save());
            save.addClickHandler(new ClickHandler() {
                public void onClick(ClickEvent event) {
                    if (!input.getValue().equals("")) {
                        ui.rpc.plsModeSave(input.getValue(),
                                new PlsCallback(ui));
                        SaveDialog.this.hide();
                    }
                }
            });
            buttonPanel.add(save);
            panel.setHorizontalAlignment(VerticalPanel.ALIGN_RIGHT);
            panel.add(buttonPanel);

            setWidget(panel);
        }
    }
    private SaveDialog saveDg;

    public PlaylistMode(WebuiLayout ui) {
        super("playlist", ui, true, true);
        saveDg = new SaveDialog(ui);
    }

    public void onClick(ClickEvent event) {
        Widget sender = (Widget) event.getSource();
        if (sender == plsShuffle) {
            ui.rpc.plsModeShuffle(new DefaultRpcCallback(ui));
        } else if (sender == plsClear) {
            ui.rpc.plsModeClear(new DefaultRpcCallback(ui));
        } else if (sender == plsRemove) {
            ui.rpc.plsModeRemove(getMediaSelection(),
                    new DefaultRpcCallback(ui));
        } else if (sender == goToCurrent) {
            if (currentPlayingPos != -1) {
                Widget wg = modeMedialist.getWidget(currentPlayingPos, 0);
                modeMedialistPanel.ensureVisible(wg);
            }
        } else if (sender == plsSave) {
            saveDg.center();
        }
    }

    void buildTopToolbar(HorizontalPanel toolbar) {
        HorizontalPanel optionPanel = new HorizontalPanel();
        optionPanel.add(makePlayorderWidget());
        optionPanel.add(makeRepeatWidget());
        toolbar.add(optionPanel);

        description = new Label();
        toolbar.setHorizontalAlignment(HorizontalPanel.ALIGN_RIGHT);
        toolbar.add(description);
    }

    void buildBottomToolbar(HorizontalPanel toolbar) {
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

    void buildHeader(FlexTable header) {
        header.getColumnFormatter().setWidth(0, "28px"); // checkbox
        header.getColumnFormatter().setWidth(1, "18px"); // play button
        header.getColumnFormatter().setWidth(2, "40px"); // tracknumber
        header.getFlexCellFormatter().setColSpan(0, 3, 2); // title
        header.getColumnFormatter().setWidth(8, "50px"); // length
        header.getColumnFormatter().setWidth(9, "65px"); // rating

        // add a checkbox
        final CheckBox allCk = new CheckBox();
        allCk.addClickHandler(new ClickHandler() {
            public void onClick(ClickEvent event) {
                boolean value = allCk.getValue();
                int size = modeMedialist.getRowCount();
                for (int idx=0; idx<size; idx++) {
                    CheckBox ck = (CheckBox) modeMedialist.getWidget(idx, 0);
                    ck.setValue(value);
                }
            }
        });
        header.setWidget(0, 0, allCk);
        // set other columns
        header.setText(0, 2, "#");
        header.setText(0, 3, ui.i18nConstants.title());
        header.setText(0, 4, ui.i18nConstants.artist());
        header.setText(0, 5, ui.i18nConstants.album());
        header.setText(0, 6, ui.i18nConstants.genre());
        header.setText(0, 7, ui.i18nConstants.length());
        header.setText(0, 8, ui.i18nConstants.rating());
    }

    void formatMedialist(FlexTable mediaList) {
        mediaList.getColumnFormatter().setWidth(0, "28px"); // checkbox
        mediaList.getColumnFormatter().setWidth(1, "18px"); // play button
        mediaList.getColumnFormatter().setWidth(2, "40px"); // tracknumber
        mediaList.getColumnFormatter().setWidth(8, "50px"); // length
        mediaList.getColumnFormatter().setWidth(9, "65px"); // rating
    }

    void buildRow(FlexTable mediaList, int idx, JSONObject media) {
        int id = (int) media.get("id").isNumber().doubleValue();
        // set style for this row
        if ((idx % 2) == 0) {
            mediaList.getRowFormatter().setStyleName(idx,
                    resources.webuiCss().oddRow());
        }

        // add a checkbox
        CheckBox checkbox = new CheckBox();
        checkbox.setFormValue(Integer.toString(id));
        mediaList.setWidget(idx, 0, checkbox);

        Image playButton = new Image(resources.medialistPlay());
        playButton.addClickHandler(new PlayRowHandler(id));
        mediaList.setWidget(idx, 1, playButton);

        mediaList.setText(idx, 2, media.get("tracknumber")
                                       .isString().stringValue());
        mediaList.getFlexCellFormatter().setColSpan(idx, 3, 2); // title
        mediaList.setText(idx, 3, media.get("title").isString().stringValue());
        mediaList.setText(idx, 4, media.get("artist").isString().stringValue());
        mediaList.setText(idx, 5, media.get("album").isString().stringValue());
        mediaList.setText(idx, 6, media.get("genre").isString().stringValue());

        // set medialength
        int length = Integer.parseInt(media.get("length").
                isString().stringValue());
        mediaList.setText(idx, 7, DeejaydUtils.formatTime(length));

        // set rating
        mediaList.setWidget(idx, 8, makeRatingWidget(media));
    }

    void setDescription(int length, int timelength) {
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
}

//vim: ts=4 sw=4 expandtab