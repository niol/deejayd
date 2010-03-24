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

import org.mroy31.deejayd.common.events.StatsChangeEvent;
import org.mroy31.deejayd.common.events.StatusChangeEvent;
import org.mroy31.deejayd.common.rpc.GenericRpcCallback;
import org.mroy31.deejayd.common.widgets.DeejaydUIWidget;
import org.mroy31.deejayd.webui.i18n.WebuiConstants;
import org.mroy31.deejayd.webui.i18n.WebuiMessages;
import org.mroy31.deejayd.webui.resources.WebuiResources;
import org.mroy31.deejayd.webui.widgets.LibraryManager;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ChangeEvent;
import com.google.gwt.event.dom.client.ChangeHandler;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiFactory;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.DockLayoutPanel;
import com.google.gwt.user.client.ui.ListBox;
import com.google.gwt.user.client.ui.Widget;

public class WebuiLayout extends DeejaydUIWidget implements ClickHandler {
    private WebuiLayout ui;
    public LibraryManager audioLibrary;

    public WebuiConstants i18nConstants = GWT.create(WebuiConstants.class);
    public WebuiMessages i18nMessages = GWT.create(WebuiMessages.class);

    private static LayoutUiBinder uiBinder = GWT.create(LayoutUiBinder.class);

    interface LayoutUiBinder extends UiBinder<DockLayoutPanel, WebuiLayout> {}

    @UiField PlayerUI playerUI;
    @UiField WebuiModeManager modeManager;
    @UiField WebuiPanelManager panelManager;
    @UiField Button refreshButton;
    @UiField ListBox modeList;
    @UiField(provided = true) public final WebuiResources resources;

    /**
     * Default rpc callback to update webui
     *
     */
    public class DefaultCallback extends GenericRpcCallback {
        public DefaultCallback(DeejaydUIWidget ui) {super(ui);}
        public void onCorrectAnswer(JSONValue data) {
            ui.update();
        }
    }

    public WebuiLayout(Deejayd_webui module) {
        ui = this;
        // load ressources
        resources = GWT.create(WebuiResources.class);
        resources.webuiCss().ensureInjected();

        initWidget(uiBinder.createAndBindUi(this));
        refreshButton.addClickHandler(this);
        refreshButton.setText(i18nConstants.refresh());

        modeList.addChangeHandler(new ChangeHandler() {
            @Override
            public void onChange(ChangeEvent event) {
                String mode = modeList.getValue(modeList.getSelectedIndex());
                rpc.setMode(mode, new DefaultCallback(ui));
            }
        });
    }

    public void onClick(ClickEvent event) {
        Widget source = (Widget) event.getSource();
        if (source == refreshButton) {
            update();
        }
    }

    @UiFactory PlayerUI makePlayerUI() {
        return new PlayerUI(this);
    }

    @UiFactory WebuiModeManager makeModeManager() {
        return new WebuiModeManager(this);
    }

    @UiFactory WebuiPanelManager makePanelManager() {
        return new WebuiPanelManager(this);
    }

    public void setMessage(String message) {
        Window.alert(message);
    }

    public void setError(String error) {
        Window.alert(error);
    }

    public void load() {
        super.load();
        // init audio library
        HashMap<String, String> messages = new HashMap<String, String>();
        messages.put("button",
                ui.i18nMessages.libUpdateButton(ui.i18nConstants.audio()));
        messages.put("confirmation",
                ui.i18nMessages.libUpdateMessage(ui.i18nConstants.audio()));
        messages.put("loading",
                ui.i18nMessages.libUpdateLoading(ui.i18nConstants.audio()));
        audioLibrary = new LibraryManager(this, "audio", messages);

        // load mode list
        class Callback extends GenericRpcCallback {
            public Callback(DeejaydUIWidget ui) {super(ui);}
            public void onCorrectAnswer(JSONValue data) {
                JSONObject list = data.isObject();
                for (String key : list.keySet()) {
                    boolean av = list.get(key).isBoolean().booleanValue();
                    if (av) {
                        modeList.addItem(key, key);
                    }
                }
            }
        }
        rpc.getModeList(new Callback(this));
        update();
    }

    @Override
    public void update() {
        class StatusCallback extends GenericRpcCallback {
            public StatusCallback(DeejaydUIWidget ui) {super(ui);}
            public void onCorrectAnswer(JSONValue data) {
                JSONObject obj = data.isObject();
                // create a java map with status
                HashMap<String, String> status = new HashMap<String, String>();
                for (String key : obj.keySet()) {
                    JSONValue value = obj.get(key);
                    if (value.isString() != null) {
                        status.put(key, value.isString().stringValue());
                    } else if (value.isNumber() != null) {
                        int number = (int) value.isNumber().doubleValue();
                        status.put(key, Integer.toString(number));
                    } else if (value.isBoolean() != null) {
                        status.put(key,
                            Boolean.toString(value.isBoolean().booleanValue()));
                    }
                }

                // select current mode
                String currentMode = status.get("mode");
                for (int idx=0; idx<modeList.getItemCount(); idx ++) {
                    if (currentMode.equals(modeList.getValue(idx))) {
                        modeList.setSelectedIndex(idx);
                        break;
                    }
                }

                fireEvent(new StatusChangeEvent(status));
            }
        }
        this.rpc.getStatus(new StatusCallback(this));

        class StatsCallback extends GenericRpcCallback {
            public StatsCallback(DeejaydUIWidget ui) {super(ui);}
            public void onCorrectAnswer(JSONValue data) {
                JSONObject obj = data.isObject();
                // create a java map with stats
                HashMap<String, String> stats = new HashMap<String, String>();
                for (String key : obj.keySet()) {
                    JSONValue value = obj.get(key);
                    if (value.isString() != null) {
                        stats.put(key, value.isString().stringValue());
                    } else if (value.isNumber() != null) {
                        int number = (int) value.isNumber().doubleValue();
                        stats.put(key, Integer.toString(number));
                    } else if (value.isBoolean() != null) {
                        stats.put(key,
                            Boolean.toString(value.isBoolean().booleanValue()));
                    }
                }
                fireEvent(new StatsChangeEvent(stats));
            }
        }
        this.rpc.getStats(new StatsCallback(this));
    }


}

//vim: ts=4 sw=4 expandtab