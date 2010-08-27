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

package org.mroy31.deejayd.webui.widgets;

import com.google.gwt.user.client.ui.SplitLayoutPanel;
import com.google.gwt.user.client.ui.Widget;

public class WebuiSplitLayoutPanel extends SplitLayoutPanel {

    public void setSplitPosition(Widget w, double size, boolean animate) {
        LayoutData layout = (LayoutData) w.getLayoutData();
        layout.oldSize = layout.size;
        layout.size=size;

        // show/hide splitter
        int idx = getWidgetIndex(w);
        if (idx < getWidgetCount() - 2) {
            Widget splitter = getWidget(idx + 1);
            LayoutData splitterLayout = (LayoutData) splitter.getLayoutData();
            splitterLayout.oldSize = splitterLayout.size;
            if (size == 0)
                splitterLayout.size = 0;
            else
                splitterLayout.size = 8;
        }

        if (animate) {
            animate(400);
        } else {
            forceLayout();
        }
    }
}

//vim: ts=4 sw=4 expandtab