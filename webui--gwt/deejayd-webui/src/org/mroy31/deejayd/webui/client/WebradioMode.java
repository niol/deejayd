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

import org.mroy31.deejayd.common.rpc.DefaultRpcCallback;
import org.mroy31.deejayd.webui.widgets.MediaList;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.FlexTable;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.Widget;

public class WebradioMode extends WebuiMode {
    private Label description;
    private Button wbClear;
    private Button wbRemove;
    private Button goToCurrent;

    private class WebradioRenderer
            implements MediaList.ModeRenderer, ClickHandler {
        @Override
        public void buildHeader(FlexTable header) {
            header.getColumnFormatter().setWidth(0, "28px"); // checkbox
            header.getColumnFormatter().setWidth(1, "18px"); // play button

            // add a checkbox
            final CheckBox allCk = new CheckBox();
            allCk.addClickHandler(new ClickHandler() {
                public void onClick(ClickEvent event) {
                    boolean value = allCk.getValue();
                    mediaList.checkRow(value);
                }
            });
            header.setWidget(0, 0, allCk);
            // set other columns
            header.setText(0, 2, ui.i18nConstants.title());
            header.setText(0, 3, ui.i18nConstants.url());
        }

        @Override
        public void buildRow(int idx, FlexTable list, JSONObject media) {
            int id = (int) media.get("id").isNumber().doubleValue();

            // add a checkbox
            CheckBox checkbox = new CheckBox();
            checkbox.setFormValue(Integer.toString(id));
            list.setWidget(idx, 0, checkbox);

            Image playButton = new Image(resources.medialistPlay());
            playButton.addClickHandler(new PlayRowHandler(id));
            list.setWidget(idx, 1, playButton);

            list.setText(idx, 2, media.get("title").isString().stringValue());
            String urlType = media.get("url-type").isString().stringValue();
            String value = "";
            if (urlType.equals("pls")) {
                value = media.get("url").isString().stringValue();
            } else if (urlType.equals("urls")) {
                JSONArray urls = media.get("urls").isArray();
                for (int i=0; i<urls.size(); i++) {
                    value += urls.get(i).isString().stringValue()+"<br/>";
                }
            }
            list.setHTML(idx, 3, value);
        }

        @Override
        public void buildToolbar(HorizontalPanel toolbar) {
            if (wbClear == null) {
                wbClear = new Button(ui.i18nConstants.clear());
                wbClear.setStyleName(
                        ui.resources.webuiCss().modeToolbarButton() + " " +
                        ui.resources.webuiCss().clearButton());
                wbClear.addClickHandler(this);
            }
            toolbar.add(wbClear);

            if (wbRemove == null) {
                wbRemove = new Button(ui.i18nConstants.remove());
                wbRemove.setStyleName(
                        ui.resources.webuiCss().modeToolbarButton() + " " +
                        ui.resources.webuiCss().removeButton());
                wbRemove.addClickHandler(this);
            }
            toolbar.add(wbRemove);

            if (goToCurrent == null) {
                goToCurrent = new Button(ui.i18nConstants.wbGoCurrent());
                goToCurrent.setStyleName(
                        ui.resources.webuiCss().modeToolbarButton() + " " +
                        ui.resources.webuiCss().gotoButton());
                goToCurrent.addClickHandler(this);
            }
            toolbar.add(goToCurrent);
        }

        @Override
        public void formatMediaList(FlexTable mediaList) {
            mediaList.getColumnFormatter().setWidth(0, "28px"); // checkbox
            mediaList.getColumnFormatter().setWidth(1, "18px"); // play button
        }

        public void onClick(ClickEvent event) {
            Widget sender = (Widget) event.getSource();
            if (sender == wbClear) {
                ui.rpc.wbModeClear(new DefaultRpcCallback(ui));
            } else if (sender == wbRemove) {
                ui.rpc.wbModeRemove(mediaList.getSelection(),
                        new DefaultRpcCallback(ui));
            } else if (sender == goToCurrent) {
                if (currentPlayingPos != -1) {
                    mediaList.goTo(currentPlayingPos);
                }
            }
        }
    }
    private WebradioRenderer renderer = new WebradioRenderer();

    public WebradioMode(WebuiLayout ui) {
        super("webradio", ui, false, false);
        mediaList.setOption(true, renderer);
    }

    @Override
    public void onStatusChange(HashMap<String, String> status) {
        super.onStatusChange(status);
        boolean en = status.get("webradiosource").equals("local");
        wbClear.setEnabled(en);
        wbRemove.setEnabled(en);
    }

    @Override
    void buildTopToolbar(HorizontalPanel toolbar) {
        description = new Label();
        toolbar.setHorizontalAlignment(HorizontalPanel.ALIGN_RIGHT);
        toolbar.add(description);
    }

    @Override
    void setDescription(int length, int timelength) {
        if (description != null) {
            description.setText(ui.i18nMessages.webradiosDesc(length));
        }
    }
}

//vim: ts=4 sw=4 expandtab