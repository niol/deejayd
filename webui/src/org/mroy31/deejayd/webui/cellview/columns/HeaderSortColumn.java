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

package org.mroy31.deejayd.webui.cellview.columns;

import org.mroy31.deejayd.webui.client.WebuiLayout;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.user.client.DOM;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;

public abstract class HeaderSortColumn extends Composite {
    protected WebuiLayout ui;

    private String[] states = {"unsorted", "ascending", "descending"};
    private int state = 0;
    private FlowPanel imgPanel = new FlowPanel();

    public HeaderSortColumn(WebuiLayout ui, String title) {
        this.ui = ui;

        Label label = new Label(title);
        HorizontalPanel panel = new HorizontalPanel();
        panel.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);
        panel.add(imgPanel);
        panel.add(label);

        panel.addDomHandler(new ClickHandler() {

            public void onClick(ClickEvent event) {
                int newState = (state + 1) % 3;
                onSortUpdate(states[newState]);
            }
        }, ClickEvent.getType());

        initWidget(panel);
        DOM.setStyleAttribute(panel.getElement(), "cursor", "pointer");
        DOM.setStyleAttribute(imgPanel.getElement(), "paddingRight", "5px");
    }

    public void setSortState(String value) {
        imgPanel.clear();
        state = 0;
        if ("ascending".equals(value)) {
            imgPanel.add(new Image(ui.resources.ascArraw()));
            state = 1;
        } else if ("descending".equals(value)) {
            imgPanel.add(new Image(ui.resources.descArraw()));
            state = 2;
        }
    }

    /**
     * Call when user click on the header if this one has sort support
     * @param value : new sort value for this column
     */
    public abstract void onSortUpdate(String value);
}

//vim: ts=4 sw=4 expandtab