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

import java.util.ArrayList;

import org.mroy31.deejayd.common.events.StatusChangeEvent;
import org.mroy31.deejayd.common.rpc.callbacks.AbstractRpcCallback;
import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.common.widgets.DeejaydUtils;
import org.mroy31.deejayd.mobile.client.MobileLayout;

import com.google.gwt.cell.client.AbstractCell;
import com.google.gwt.cell.client.ValueUpdater;
import com.google.gwt.dom.client.Element;
import com.google.gwt.dom.client.NativeEvent;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.cellview.client.CellList;
import com.google.gwt.user.cellview.client.HasKeyboardSelectionPolicy.KeyboardSelectionPolicy;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.HorizontalPanel;

public class DvdMode extends AbstractMode {
    private final MobileLayout ui = MobileLayout.getInstance();
    private int sourceId = -1;
    private CellList<JSONObject> mediaList = new CellList<JSONObject>(
    		new AbstractCell<JSONObject>("click") {

    			@Override
    			public void onBrowserEvent(Context context, Element parent, JSONObject track,
    				      NativeEvent event, ValueUpdater<JSONObject> valueUpdater) {
    				ui.rpc.goTo((int) track.get("ix").isNumber().doubleValue(),
                            new AnswerHandler<Boolean>() {
                        public void onAnswer(Boolean answer) {
                            ui.update();
                            ui.getWallPanel("currentMode").showChild();
                        }
                    });
    				
    			}
    			
				@Override
				public void render(com.google.gwt.cell.client.Cell.Context context,
						JSONObject track, SafeHtmlBuilder sb) {
					int idx = (int) track.get("ix").isNumber().doubleValue();
					String label = ui.i18nConst.title()+" "+Integer.toString(idx)+
    		                " ("+DeejaydUtils.formatTime((int) track.get("length").
    		                         isNumber().doubleValue())+")";
					sb.appendEscaped(label);
				}
	});
    private HorizontalPanel toolbar = new HorizontalPanel();

    public DvdMode() {
        toolbar.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);
        toolbar.setSpacing(5);
        Button reload = new Button();
        reload.addStyleName(ui.resources.mobileCss().playerButton());
        reload.addStyleName(ui.resources.mobileCss().shuffle());
        reload.addClickHandler(new ClickHandler() {
            public void onClick(ClickEvent event) {
                ui.rpc.dvdModeReload();
            }
        });
        toolbar.add(reload);

        FlowPanel panel = new FlowPanel();
        
        mediaList.setPageSize(100);
        mediaList.setKeyboardSelectionPolicy(KeyboardSelectionPolicy.DISABLED);
        panel.add(toolbar);
        panel.add(mediaList);
        initWidget(panel);

        ui.addStatusChangeHandler(this);
    }

    public void onStatusChange(StatusChangeEvent event) {
        int id = Integer.parseInt(event.getStatus().get("dvd"));
        if (id != sourceId) {
            ui.rpc.send("dvd.get", new JSONArray(), new AbstractRpcCallback() {

                @Override
                public void onCorrectAnswer(JSONValue data) {
                	ArrayList<JSONObject> trackObjs = new ArrayList<JSONObject>();
                    JSONArray tracks = data.isObject().get("track").isArray();
                    for (int i = 0; i<tracks.size(); i++) {
                        JSONObject track = tracks.get(i).isObject();
                        trackObjs.add(track);
                    }
                    mediaList.setRowData(trackObjs);
                }
            });

            sourceId = id;
        }
    }

    @Override
    public String getTitle() {
        return ui.i18nConst.dvd();
    }

}

//vim: ts=4 sw=4 expandtab