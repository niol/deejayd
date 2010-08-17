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

package org.mroy31.deejayd.mobile.client;

import java.util.HashMap;

import org.mroy31.deejayd.common.events.StatusChangeEvent;
import org.mroy31.deejayd.common.rpc.DefaultRpcCallback;
import org.mroy31.deejayd.common.widgets.DeejaydUIWidget;
import org.mroy31.deejayd.mobile.i18n.MobileConstants;
import org.mroy31.deejayd.mobile.resources.MobileResources;
import org.mroy31.deejayd.mobile.widgets.ScrollToCommand;
import org.mroy31.deejayd.mobile.widgets.WallToWallPanel;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Command;
import com.google.gwt.user.client.DeferredCommand;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.Widget;

public class MobileLayout extends DeejaydUIWidget {
    static private MobileLayout instance;
    public final MobileConstants i18nConst = GWT.create(MobileConstants.class);
    public final MobileResources resources = GWT.create(MobileResources.class);

    private class Message extends Composite {

        public Message(String text, String type) {
            HorizontalPanel msgPanel = new HorizontalPanel();
            msgPanel.addStyleName(resources.mobileCss().msgPanel());
            msgPanel.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);
            msgPanel.setSpacing(4);

            Label msgLabel = new Label(text);
            msgPanel.add(msgLabel);
            msgPanel.setCellWidth(msgLabel, "100%");
            Button close = new Button(i18nConst.close());
            close.addClickHandler(new ClickHandler() {
                @Override
                public void onClick(ClickEvent event) {
                    event.preventDefault();
                    event.stopPropagation();

                    removeFromParent();
                }
            });
            msgPanel.add(close);

            if (type.equals("error")) {
                msgPanel.addStyleName(resources.mobileCss().error());
            } else if (type.equals("information")) {
                msgPanel.addStyleName(resources.mobileCss().information());
            }

            initWidget(msgPanel);
            if (!type.equals("error")) {
                Timer timer = new Timer() {
                    @Override
                    public void run() {
                        removeFromParent();
                    }
                };
                timer.schedule(5000);
            }
        }
    }

    private final FlowPanel panel = new FlowPanel();
    private HashMap<String, WallToWallPanel> walls =
        new HashMap<String, WallToWallPanel>();

    static public MobileLayout getInstance() {
        if (instance == null)
            instance = new MobileLayout();
        return instance;
    }

    public MobileLayout() {
        resources.mobileCss().ensureInjected();
        panel.addStyleName(resources.mobileCss().mainBody());

        initWidget(panel);
        DeferredCommand.addCommand(new Command() {
            @Override
            public void execute() {
                ModeListPanel modeList = new ModeListPanel();
                walls.put("modeList", modeList);
                panel.add(modeList);

                SourcePanel source = new SourcePanel(modeList);
                walls.put("currentMode", source);
                panel.add(source);

                PlayerPanel player = new PlayerPanel(source);
                walls.put("player", player);
                panel.add(player);

                player.addStyleName(resources.mobileCss().currentWall());
            }
        });
        DeferredCommand.addCommand(new Command() {
            @Override
            public void execute() {
                update();
            }
        });
        DeferredCommand.addPause();
        DeferredCommand.addPause();
        DeferredCommand.addCommand(new ScrollToCommand(null));
    }

    public WallToWallPanel getWallPanel(String name) {
        return walls.get(name);
    }

    public void addWidget(Widget w) {
        panel.add(w);
    }

    @Override
    public void setError(String error) {
        panel.add(new Message(error, "error"));
    }

    @Override
    public void setMessage(String message) {
        panel.add(new Message(message, "information"));
    }

    @Override
    public void update() {
        class StatusCallback extends DefaultRpcCallback {
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

                fireEvent(new StatusChangeEvent(status));
            }
        }
        this.rpc.getStatus(new StatusCallback(this));
    }

    public String getSourceTitle(String source) {
        if (source.equals("panel")) {
            return i18nConst.panel();
        } else if (source.equals("playlist")) {
            return i18nConst.playlist();
        } else if (source.equals("webradio")) {
            return i18nConst.webradio();
        } else if (source.equals("video")) {
            return i18nConst.videoMode();
        } else if (source.equals("dvd")) {
            return i18nConst.dvd();
        }
        return "";
    }
}

//vim: ts=4 sw=4 expandtab