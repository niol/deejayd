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

import org.mroy31.deejayd.common.rpc.GenericRpcCallback;
import org.mroy31.deejayd.mobile.widgets.ListPanel;
import org.mroy31.deejayd.mobile.widgets.WallToWallPanel;

import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.DOM;
import com.google.gwt.user.client.Event;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;

public class ModeListPanel extends WallToWallPanel {
    private class ModeItem extends Composite {
        private final String mode;

        public ModeItem(String mode) {
            this.mode = mode;
            HorizontalPanel panel = new HorizontalPanel();
            Label modeLabel = new Label(ui.getSourceTitle(mode));

            panel.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);
            panel.addStyleName(ui.resources.mobileCss().modeListDesc());
            panel.setWidth("100%");
            panel.add(modeLabel);
            panel.setCellWidth(modeLabel, "100%");
            panel.add(new Image(ui.resources.chevron()));

            initWidget(panel);
            addStyleName(ui.resources.mobileCss().modeListItem());
            sinkEvents(Event.ONCLICK);
        }

        @Override
        public void onBrowserEvent(Event event) {
            super.onBrowserEvent(event);
            switch (DOM.eventGetType(event)) {
                case Event.ONCLICK:
                    ui.rpc.setMode(mode, new GenericRpcCallback() {

                        @Override
                        public void setError(String error) {
                            ui.setError(error);
                        }

                        @Override
                        public void onCorrectAnswer(JSONValue data) {
                            ui.update();
                            showChild();
                        }
                    });
                    break;
            }
        }
    }

    public ModeListPanel() {
        super("Mode List", null);

        // build mode list
        ui.rpc.getModeList(new GenericRpcCallback() {

            @Override
            public void setError(String error) {
                ui.setError(error);
            }

            @Override
            public void onCorrectAnswer(JSONValue data) {
                ListPanel panel = new ListPanel();
                JSONObject list = data.isObject();

                for (String key : list.keySet()) {
                    boolean av = list.get(key).isBoolean().booleanValue();
                    if (av) {
                        panel.add(new ModeItem(key));
                    }
                }
                add(panel);
            }
        });
    }

    @Override
    protected String getShortTitle() {
        return ui.i18nConst.list();
    }

}

//vim: ts=4 sw=4 expandtab