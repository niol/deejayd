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
import org.mroy31.deejayd.common.widgets.DeejaydSelModel;

import com.google.gwt.cell.client.AbstractCell;
import com.google.gwt.cell.client.ValueUpdater;
import com.google.gwt.dom.client.Element;
import com.google.gwt.dom.client.NativeEvent;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.cellview.client.DeejaydCellTable;

public class GrippyCell<T> extends AbstractCell<String> {
    private final DeejaydCellTable<T> view;
    private final String className;

    public static interface DragStartMessage {
        public String onDragStart(int count);
    }
    private DragStartMessage msg;

    public GrippyCell(DeejaydCellTable<T> view, String className,
            DragStartMessage msg) {
        super("dragstart", "dragend");
        this.className = className;
        this.view = view;
        this.msg = msg;
    }

    @Override
    public boolean handlesSelection() {
        return true;
    }

    @Override
    public void render(String value, Object key, SafeHtmlBuilder sb) {
        sb.appendHtmlConstant("<span style='margin-left:6px;margin-right:6px;'>");
        sb.appendHtmlConstant("<img draggable=\"true\" src=\"./deejayd_webui/clear.cache.gif\" class=\""+className+"\">")
          .appendHtmlConstant("</img>")
          .appendHtmlConstant("</span>");
    }

    @Override
    public void onBrowserEvent(Element parent, String value, Object key,
              NativeEvent event, ValueUpdater<String> valueUpdater) {
        if ("dragstart".equals(event.getType())) {
            boolean needCheck = false;
            int selCount = 0;
            for (T item : view.getDisplayedItems()) {
                String v = (String) view.getKeyProvider().getKey(item);
                if (view.getSelectionModel().isSelected(item)) {
                    ++selCount;
                    if (!v.equals(key))
                        value += "///" + v;
                }
                else if (v.equals(key)
                        && !view.getSelectionModel().isSelected(item)) {
                    ++selCount;
                    needCheck = true;
                }
            }
            DragStartEvent evt = new DragStartEvent();
            evt.setNativeEvent(event);
            evt.dataTransfert().setData(value);
            evt.dataTransfert().setDragImage(msg.onDragStart(selCount));

            if (needCheck)
                valueUpdater.update("true");
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