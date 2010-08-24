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

import org.mroy31.deejayd.common.rpc.GenericRpcCallback;
import org.mroy31.deejayd.mobile.client.MobileLayout;

import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.DOM;
import com.google.gwt.user.client.Event;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;

public class MediaItem extends Composite {
    private final MobileLayout ui = MobileLayout.getInstance();
    private int id;

    public MediaItem(int id, String title, String desc) {
        this.id = id;
        HorizontalPanel panel = new HorizontalPanel();
        panel.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);
        panel.setWidth("100%");

        FlowPanel tPanel = new FlowPanel();
        tPanel.setWidth(Integer.toString(Window.getClientWidth()-100) + "px");
        HTML lTitle = new HTML(title);
        lTitle.addStyleName(ui.resources.mobileCss().mListTitle());
        tPanel.add(lTitle);

        HTML lDesc = new HTML(desc);
        lDesc.addStyleName(ui.resources.mobileCss().mListDesc());
        tPanel.add(lDesc);

        panel.add(tPanel);
        panel.setCellWidth(tPanel, "100%");
        panel.add(new Image(ui.resources.chevron()));
        initWidget(panel);
        addStyleName(ui.resources.mobileCss().mListItem());

        sinkEvents(Event.ONCLICK);
    }

    @Override
    public void onBrowserEvent(Event event) {
        switch (DOM.eventGetType(event)) {
        case Event.ONCLICK:
            ui.rpc.goTo(id, new GenericRpcCallback() {

                @Override
                public void setError(String error) {
                    ui.setError(error);
                }

                @Override
                public void onCorrectAnswer(JSONValue data) {
                    ui.update();
                    ui.getWallPanel("currentMode").showChild();
                }
            });
            break;
        }
    }
}

//vim: ts=4 sw=4 expandtab