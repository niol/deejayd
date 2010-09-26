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

import org.mroy31.deejayd.common.events.DragStartEvent;
import org.mroy31.deejayd.webui.cellview.DeejaydSelModel;

import com.google.gwt.cell.client.AbstractCell;
import com.google.gwt.cell.client.ValueUpdater;
import com.google.gwt.dom.client.Element;
import com.google.gwt.dom.client.NativeEvent;
import com.google.gwt.resources.client.ImageResource;
import com.google.gwt.user.cellview.client.DeejaydCellTable;
import com.google.gwt.user.client.ui.AbstractImagePrototype;

public class GrippyCell<T> extends AbstractCell<String> {
    private final DeejaydCellTable<T> view;
    private final String imgHtml;

    public GrippyCell(DeejaydCellTable<T> view, ImageResource img) {
        super("dragstart", "dragend");
        imgHtml = AbstractImagePrototype.create(img).getHTML();

        this.view = view;
    }

    @Override
    public void render(String value, Object key, StringBuilder sb) {
        sb.append("<span draggable='true' style='-webkit-user-drag: element;");
        sb.append(" margin:0px 4px; cursor:move;'>");
        sb.append(imgHtml);
        sb.append("</span>");
    }

    @Override
    public void onBrowserEvent(Element parent, String value, Object key,
              NativeEvent event, ValueUpdater<String> valueUpdater) {
        if ("dragstart".equals(event.getType())) {
            for (T item : view.getDisplayedItems()) {
                String v = (String) view.getKeyProvider().getKey(item);
                if (view.getSelectionModel().isSelected(item)
                            && !v.equals(key))
                    value += "///" + v;
                else if (v.equals(key)
                        && !view.getSelectionModel().isSelected(item)) {
                    // the row is not selected, disable the drag action
                    event.preventDefault();
                    return;
                }
            }
            DragStartEvent evt = new DragStartEvent();
            evt.setNativeEvent(event);
            evt.dataTransfert().setData(value);
        } else if ("dragend".equals(event.getType())) {
            DragStartEvent evt = new DragStartEvent();
            evt.setNativeEvent(event);
            if (!evt.dataTransfert().getDropEffect().equals("none")) {
                @SuppressWarnings("unchecked")
                DeejaydSelModel<T> sel = (DeejaydSelModel<T>) view.getSelectionModel();
                sel.clearSelection();
            }

        }
    }

}

//vim: ts=4 sw=4 expandtab