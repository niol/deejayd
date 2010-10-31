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

import org.mroy31.deejayd.common.rpc.callbacks.RpcHandler;
import org.mroy31.deejayd.common.widgets.DeejaydUIWidget;
import org.mroy31.deejayd.mobile.i18n.MobileConstants;
import org.mroy31.deejayd.mobile.resources.MobileResources;
import org.mroy31.deejayd.mobile.widgets.ScrollToCommand;
import org.mroy31.deejayd.mobile.widgets.WallToWallPanel;

import com.google.gwt.core.client.GWT;
import com.google.gwt.core.client.Scheduler;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.user.client.Command;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.Widget;

public class MobileLayout extends DeejaydUIWidget {
    static private MobileLayout instance;
    public final MobileConstants i18nConst = GWT.create(MobileConstants.class);
    public final MobileResources resources = GWT.create(MobileResources.class);

    private class MobileMessage extends Message {

        public MobileMessage(String message, String type) {
            super(message, type);
        }

        @Override
        protected Widget buildWidget(String message, String type) {
            HorizontalPanel msgPanel = new HorizontalPanel();
            msgPanel.addStyleName(resources.mobileCss().msgPanel());
            msgPanel.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);
            msgPanel.setSpacing(4);

            Label msgLabel = new Label(message);
            msgPanel.add(msgLabel);
            msgPanel.setCellWidth(msgLabel, "100%");
            Button close = new Button(i18nConst.close());
            close.addClickHandler(new ClickHandler() {
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

            return msgPanel;
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
        this.rpc.addRpcHandler(new RpcHandler() {

            public void onRpcStop() {}
            public void onRpcStart() {}

            public void onRpcError(String error) {
                setMessage(error, "error");
            }
        });

        resources.mobileCss().ensureInjected();
        panel.addStyleName(resources.mobileCss().mainBody());

        initWidget(panel);
        Scheduler.get().scheduleDeferred(new Command() {
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
        Scheduler.get().scheduleDeferred(new Command() {
            public void execute() {
                update();
            }
        });
        Scheduler.get().scheduleDeferred(new ScrollToCommand(null));
    }

    public WallToWallPanel getWallPanel(String name) {
        return walls.get(name);
    }

    public void addWidget(Widget w) {
        panel.add(w);
    }

    @Override
    public void setMessage(String message, String type) {
        panel.add(new MobileMessage(message, type));
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