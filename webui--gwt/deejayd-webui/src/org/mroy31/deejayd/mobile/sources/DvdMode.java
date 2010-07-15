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

package org.mroy31.deejayd.mobile.sources;

import org.mroy31.deejayd.common.events.StatusChangeEvent;
import org.mroy31.deejayd.common.rpc.GenericRpcCallback;
import org.mroy31.deejayd.mobile.client.MobileLayout;
import org.mroy31.deejayd.mobile.widgets.ListPanel;
import org.mroy31.deejayd.mobile.widgets.LoadingWidget;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.Label;

public class DvdMode extends DeejaydMode {
    private final MobileLayout ui = MobileLayout.getInstance();
    private int sourceId = -1;
    private ListPanel mediaList = new ListPanel();

    public DvdMode() {
        FlowPanel panel = new FlowPanel();
        panel.add(mediaList);
        initWidget(panel);

        ui.addStatusChangeHandler(this);
    }

    @Override
    public void onStatusChange(StatusChangeEvent event) {
        int id = Integer.parseInt(event.getStatus().get("dvd"));
        if (id != sourceId) {
            mediaList.clear();
            mediaList.add(new LoadingWidget());
            ui.rpc.send("dvd.get", new JSONArray(), new GenericRpcCallback() {

                @Override
                public void setError(String error) {
                    ui.setError(error);
                }

                @Override
                public void onCorrectAnswer(JSONValue data) {
                    mediaList.clear();
                    JSONArray tracks = data.isObject().get("track").isArray();
                    for (int i = 0; i<tracks.size(); i++) {
                        JSONObject track = tracks.get(i).isObject();
                        addRow(track, i);
                    }
                }
            });

            sourceId = id;
        }
    }

    @Override
    public String getTitle() {
        return ui.i18nConst.dvd();
    }

    private void addRow(final JSONObject track, int idx) {
        Label l = new Label(ui.i18nConst.title()+" "+Integer.toString(idx));
        l.addStyleName(ui.resources.mobileCss().dvdTrack());
        l.addClickHandler(new ClickHandler() {
            @Override
            public void onClick(ClickEvent event) {
            }
        });

        mediaList.add(l);
    }
}

//vim: ts=4 sw=4 expandtab