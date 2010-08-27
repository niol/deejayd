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

package org.mroy31.deejayd.common.events;

import java.util.HashMap;

import com.google.gwt.event.shared.GwtEvent;
import com.google.gwt.event.shared.HasHandlers;

public class StatusChangeEvent extends GwtEvent<StatusChangeHandler>{
    private HashMap<String, String> status;
    public static final Type<StatusChangeHandler> TYPE = new Type<StatusChangeHandler>();


    public StatusChangeEvent(HashMap<String, String> status) {
        super();
        this.status = status;
    }

    public HashMap<String, String> getStatus() {
        return status;
    }

    @Override
    protected void dispatch(StatusChangeHandler handler) {
        handler.onStatusChange(this);
    }

    @Override
    public final Type<StatusChangeHandler> getAssociatedType() {
        return TYPE;
    }

    public static Type<StatusChangeHandler> getType() {
        return TYPE;
    }

    public static <S extends HasStatusChangeHandlers & HasHandlers>
        void fire(S source, HashMap<String, String> status) {
        StatusChangeEvent event = new StatusChangeEvent(status);
        source.fireEvent(event);
    }
}

//vim: ts=4 sw=4 expandtab