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

import com.google.gwt.event.shared.GwtEvent;
import com.google.gwt.event.shared.HasHandlers;

public class LibraryChangeEvent extends GwtEvent<LibraryChangeHandler>{
    private String libraryType;
    public static final Type<LibraryChangeHandler> TYPE =
        new Type<LibraryChangeHandler>();


    public LibraryChangeEvent(String libType) {
        super();
        this.libraryType = libType;
    }

    public String getLibraryType() {
        return libraryType;
    }

    @Override
    protected void dispatch(LibraryChangeHandler handler) {
        handler.onLibraryChange(this);
    }

    @Override
    public final Type<LibraryChangeHandler> getAssociatedType() {
        return TYPE;
    }

    public static Type<LibraryChangeHandler> getType() {
        return TYPE;
    }

    public static <S extends HasLibraryChangeHandlers & HasHandlers>
        void fire(S source, String libType) {
        LibraryChangeEvent event = new LibraryChangeEvent(libType);
        source.fireEvent(event);
    }
}

//vim: ts=4 sw=4 expandtab