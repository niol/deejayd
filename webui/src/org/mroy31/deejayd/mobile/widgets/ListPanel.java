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

import com.google.gwt.user.client.DOM;
import com.google.gwt.user.client.ui.ComplexPanel;
import com.google.gwt.user.client.ui.Widget;

public class ListPanel extends ComplexPanel {
    private class ListItem extends ComplexPanel {
        public ListItem(Widget w) {
            setElement(DOM.createElement("li"));
            add(w, getElement());
        }
    }

    public ListPanel() {
        setElement(DOM.createElement("ul"));
        addStyleName(MobileLayout.getInstance().resources.mobileCss().listPanel());
    }

    @Override
    public void add(Widget w) {
        add(new ListItem(w), getElement());
    }

    public void insert(Widget w, int beforeIndex) {
        insert(w, getElement(), beforeIndex, true);
    }

    @Override
    public Widget getWidget(int idx) {
        ListItem item = (ListItem) super.getWidget(idx);

        return item.getWidget(0);
    }
}

//vim: ts=4 sw=4 expandtab