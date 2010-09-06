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

import org.mroy31.deejayd.common.rpc.callbacks.AbstractRpcCallback;
import org.mroy31.deejayd.common.widgets.DeejaydUtils;
import org.mroy31.deejayd.webui.resources.WebuiResources;
import org.mroy31.deejayd.webui.widgets.LoadingWidget;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiFactory;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.DOM;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.Tree;
import com.google.gwt.user.client.ui.TreeItem;
import com.google.gwt.user.client.ui.Widget;

public class DvdMode extends Composite implements WebuiModeInterface {
    private WebuiLayout webui;
    private int dvdId;

    private static DvdModeUiBinder uiBinder = GWT.create(DvdModeUiBinder.class);
    interface DvdModeUiBinder extends UiBinder<Widget, DvdMode> {}


    private class InfoCallback extends AbstractRpcCallback {

        private class DvdItem extends HorizontalPanel {
            public DvdItem(String title, int length, final String id) {
                setVerticalAlignment(ALIGN_MIDDLE);

                Image playButton = new Image(webui.resources.playLow());
                playButton.addClickHandler(new ClickHandler() {
                    public void onClick(ClickEvent event) {
                        webui.rpc.goTo(id, null);
                    }
                });
                add(playButton);

                String tDesc = DeejaydUtils.formatTimeLong(length,
                        webui.i18nMessages);
                Label tLabel = new Label(title+
                        (tDesc.equals("") ? "" : " ("+tDesc+")"));
                DOM.setStyleAttribute(tLabel.getElement(),
                        "paddingRight", "10px");
                add(tLabel);
            }

        }

        @Override
        public void onCorrectAnswer(JSONValue data) {
            dvdTree.clear();
            JSONArray tracks = data.isObject().get("track").isArray();
            for (int idx=0; idx<tracks.size(); idx++) {
                JSONObject tObj = tracks.get(idx).isObject();
                int length = (int) tObj.get("length").isNumber().doubleValue();
                int id = (int) tObj.get("ix").isNumber().doubleValue();
                JSONArray chapters = tObj.get("chapter").isArray();

                TreeItem trackItem = new TreeItem(new DvdItem(
                        webui.i18nMessages.dvdTrack(idx), length,
                        Integer.toString(id)));
                for (int cIdx=0; cIdx<chapters.size(); cIdx++) {
                    JSONObject cObj = chapters.get(cIdx).isObject();
                    int cLength = (int) cObj.get("length").isNumber()
                                                          .doubleValue();
                    int cId = (int) cObj.get("ix").isNumber().doubleValue();

                    TreeItem chapterItem = new TreeItem(new DvdItem(
                            webui.i18nMessages.dvdChapter(cIdx), cLength,
                            Integer.toString(id)+"."+Integer.toString(cId)));
                    trackItem.addItem(chapterItem);
                }
                dvdTree.addItem(trackItem);
            }

            // set description
            description.setText(webui.i18nMessages.tracksDesc(tracks.size()));

            // set title
            title.setText(data.isObject().get("title").isString().stringValue());
        }
    }

    @UiField Tree dvdTree;
    @UiField HorizontalPanel topPanel;
    @UiField HorizontalPanel titlePanel;
    @UiField Label title;
    @UiField HorizontalPanel descPanel;
    @UiField Label description;
    @UiField(provided = true) final WebuiResources resources;
    @UiFactory HorizontalPanel makeHPanel() {
        HorizontalPanel panel = new HorizontalPanel();
        panel.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);

        return panel;
    }


    public DvdMode(WebuiLayout webui) {
        this.webui = webui;
        this.resources = webui.resources;
        initWidget(uiBinder.createAndBindUi(this));

        topPanel.setCellHorizontalAlignment(descPanel,
                HorizontalPanel.ALIGN_RIGHT);
        DOM.setStyleAttribute(description.getElement(), "paddingRight", "5px");
        DOM.setStyleAttribute(title.getElement(), "paddingLeft", "3px");
    }


    public String getSourceName() {
        return "dvd";
    }

    public void onStatusChange(HashMap<String, String> status) {
        int id = Integer.parseInt(status.get("dvd"));
        if (id != dvdId) {
            dvdTree.clear();
            dvdTree.addItem(new LoadingWidget(webui.i18nConstants.loading(),
                    webui.resources));
            webui.rpc.dvdGetInfo(new InfoCallback());
            dvdId = id;
        }
    }
}

//vim: ts=4 sw=4 expandtab