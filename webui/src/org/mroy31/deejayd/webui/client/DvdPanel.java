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

import com.google.gwt.dom.client.Style.Unit;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.DockLayoutPanel;
import com.google.gwt.user.client.ui.FlowPanel;

public class DvdPanel extends WebuiPanel {
    private WebuiLayout ui;

    private DockLayoutPanel dockPanel = new DockLayoutPanel(Unit.PX);
    private Button reloadButton;
    private FlowPanel bluePanel = new FlowPanel();

    public DvdPanel(WebuiLayout webui) {
        super("dvd");
        this.ui = webui;

        reloadButton = new Button(ui.i18nConstants.reload(),new ClickHandler() {
            public void onClick(ClickEvent event) {
                ui.rpc.dvdModeReload(new DefaultRpcCallback(ui));
            }
        });
        reloadButton.setWidth("100%");
        dockPanel.addNorth(reloadButton, 22);

        bluePanel.setWidth("100%");
        bluePanel.setHeight("100%");
        bluePanel.addStyleName(ui.resources.webuiCss().blueToolbar());
        dockPanel.add(bluePanel);

        initWidget(dockPanel);
    }
}

//vim: ts=4 sw=4 expandtab