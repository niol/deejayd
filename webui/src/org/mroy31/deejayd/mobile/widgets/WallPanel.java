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

package org.mroy31.deejayd.mobile.widgets;

import org.mroy31.deejayd.mobile.client.MobileLayout;
import org.mroy31.deejayd.mobile.resources.MobileResources;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiFactory;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.Command;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.Widget;

public class WallPanel extends Composite {
    private final MobileLayout ui = MobileLayout.getInstance();
    final String TITLE_W = Integer.toString(Window.getClientWidth()-170)+"px";

    private static WallPanelUiBinder uiBinder = GWT
            .create(WallPanelUiBinder.class);
    interface WallPanelUiBinder extends UiBinder<Widget, WallPanel> {}

    @UiField FlowPanel rootPanel;
    @UiField HorizontalPanel header;
    @UiField FlowPanel contents;
    @UiField HTML title;
    @UiField(provided = true) final MobileResources resources = ui.resources;

    public WallPanel() {
        initWidget(uiBinder.createAndBindUi(this));

        header.setCellWidth(title, "100%");
        header.setCellHorizontalAlignment(title, HorizontalPanel.ALIGN_CENTER);
        title.setWidth(TITLE_W);
    }

    @UiFactory public HorizontalPanel makeHPanel() {
        HorizontalPanel hPanel = new HorizontalPanel();
        hPanel.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);

        return hPanel;
    }

    @Override
    public void setTitle(String t) {
        setTitle(t, false);
    }

    public void setTitle(String t, boolean html) {
        if (html) {
            title.removeStyleName(ui.resources.mobileCss().wallHeaderTitle());
            title.addStyleName(ui.resources.mobileCss().wallHeaderHTMLTitle());
            title.setHTML(t);

        } else {
            title.removeStyleName(ui.resources.mobileCss().wallHeaderHTMLTitle());
            title.addStyleName(ui.resources.mobileCss().wallHeaderTitle());
            title.setText(t);
        }
    }

    public void setContents(Widget w) {
        contents.clear();
        contents.add(w);
    }

    public Widget getContents() {
        return contents;
    }

    public void setLeftButton(String label, final Command cmd) {
        Label l = new Label(label);
        l.addStyleName(resources.mobileCss().button());
        l.addStyleName(resources.mobileCss().headerBackButton());
        l.addClickHandler(new ClickHandler() {
            public void onClick(ClickEvent event) {
                cmd.execute();
            }
        });
        header.insert(l, 0);
    }

    public void setRightButton(String label, final Command cmd, boolean fwd) {
        Label l = new Label(label);
        l.addStyleName(resources.mobileCss().button());
        if (fwd) {
            l.addStyleName(ui.resources.mobileCss().headerForwardButton());
        }
        l.addClickHandler(new ClickHandler() {
            public void onClick(ClickEvent event) {
                cmd.execute();
            }
        });
        header.add(l);
        header.setCellHorizontalAlignment(l, HorizontalPanel.ALIGN_RIGHT);
    }

    public void setContextPanel(Widget w) {
        rootPanel.add(w);
    }
}

//vim: ts=4 sw=4 expandtab