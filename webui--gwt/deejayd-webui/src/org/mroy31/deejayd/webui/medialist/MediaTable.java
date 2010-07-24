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

package org.mroy31.deejayd.webui.medialist;

import org.mroy31.deejayd.webui.events.DragEnterEvent;
import org.mroy31.deejayd.webui.events.DragEnterHandler;
import org.mroy31.deejayd.webui.events.DragLeaveEvent;
import org.mroy31.deejayd.webui.events.DragLeaveHandler;
import org.mroy31.deejayd.webui.events.DragOverEvent;
import org.mroy31.deejayd.webui.events.DragOverHandler;
import org.mroy31.deejayd.webui.events.DropEvent;
import org.mroy31.deejayd.webui.events.DropHandler;
import org.mroy31.deejayd.webui.events.HasDropHandlers;

import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.user.client.DOM;
import com.google.gwt.user.client.Element;
import com.google.gwt.user.client.Event;
import com.google.gwt.user.client.ui.FlexTable;

public class MediaTable extends FlexTable implements HasDropHandlers {

    public int getRowForDragOverEvent(DragOverEvent event) {
        Element td = getEventTargetCell(Event.as(event.getNativeEvent()));
        if (td == null) {
          return -1;
        }

        Element tr = DOM.getParent(td);
        Element body = DOM.getParent(tr);

        return DOM.getChildIndex(body, tr);
    }

    public int getRowForDropEvent(DropEvent event) {
        Element td = getEventTargetCell(Event.as(event.getNativeEvent()));
        if (td == null) {
          return -1;
        }

        Element tr = DOM.getParent(td);
        Element body = DOM.getParent(tr);

        return DOM.getChildIndex(body, tr);
    }

    @Override
    public HandlerRegistration addDragEnterHandler(DragEnterHandler handler) {
        return addDomHandler(handler, DragEnterEvent.getType());
    }

    @Override
    public HandlerRegistration addDragLeaveHandler(DragLeaveHandler handler) {
        return addDomHandler(handler, DragLeaveEvent.getType());
    }

    @Override
    public HandlerRegistration addDragOverHandler(DragOverHandler handler) {
        return addDomHandler(handler, DragOverEvent.getType());
    }

    @Override
    public HandlerRegistration addDropHandler(DropHandler handler) {
        return addDomHandler(handler, DropEvent.getType());
    }
}

//vim: ts=4 sw=4 expandtab