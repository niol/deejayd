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

import com.google.gwt.core.client.JavaScriptObject;
import com.google.gwt.user.client.Element;

public class DataTransfert extends JavaScriptObject {

    protected DataTransfert() {}

    public final native void setData(String data) /*-{
      this.setData("text/plain", data);
    }-*/;

    public final native String getData() /*-{
        return this.getData("text/plain");
    }-*/;

    public final native void setDragImage(Element elt) /*-{
        this.setDragImage(elt, 0, 0);
    }-*/;

    public final native void setEffectAllowed(String effect) /*-{
        this.effectAlowed = effect;
    }-*/;

    public final native void setDropEffect(String effect) /*-{
        this.dropEffect = effect;
    }-*/;

    public final native String getDropEffect() /*-{
        return this.dropEffect;
    }-*/;
}

//vim: ts=4 sw=4 expandtab