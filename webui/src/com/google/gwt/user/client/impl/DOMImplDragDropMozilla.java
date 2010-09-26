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

package com.google.gwt.user.client.impl;

import com.google.gwt.user.client.Element;

/**
 * Add handling for drag and drop events to standard DOM impl used by Mozilla.
 *
 * @author Mickaël Royer
 */

public class DOMImplDragDropMozilla extends DOMImplMozilla {

    @Override
    public native int eventGetTypeInt(String eventType) /*-{
    switch (eventType) {
    case "blur": return 0x01000;
    case "change": return 0x00400;
    case "click": return 0x00001;
    case "dblclick": return 0x00002;
    case "focus": return 0x00800;
    case "keydown": return 0x00080;
    case "keypress": return 0x00100;
    case "keyup": return 0x00200;
    case "load": return 0x08000;
    case "losecapture": return 0x02000;
    case "mousedown": return 0x00004;
    case "mousemove": return 0x00040;
    case "mouseout": return 0x00020;
    case "mouseover": return 0x00010;
    case "mouseup": return 0x00008;
    case "scroll": return 0x04000;
    case "error": return 0x10000;
    case "mousewheel": return 0x20000;
    case "DOMMouseScroll": return 0x20000;
    case "contextmenu": return 0x40000;
    case "paste": return 0x80000;

    // Drag and drop events
    case "dragstart": return 0x1000000;
    case "dragend": return 0x20000000;
    case "dragover": return 0x2000000;
    case "dragenter": return 0x4000000;
    case "dragleave": return 0x8000000;
    case "drop": return 0x10000000;
    }
  }-*/;

  @Override
protected native void sinkEventsImpl(Element elem, int bits) /*-{
    var chMask = (elem.__eventBits || 0) ^ bits;
    elem.__eventBits = bits;
    if (!chMask) return;

    if (chMask & 0x00001) elem.onclick       = (bits & 0x00001) ?
        @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent : null;
    if (chMask & 0x00002) elem.ondblclick    = (bits & 0x00002) ?
        @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent : null;
    if (chMask & 0x00004) elem.onmousedown   = (bits & 0x00004) ?
        @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent : null;
    if (chMask & 0x00008) elem.onmouseup     = (bits & 0x00008) ?
        @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent : null;
    if (chMask & 0x00010) elem.onmouseover   = (bits & 0x00010) ?
        @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent : null;
    if (chMask & 0x00020) elem.onmouseout    = (bits & 0x00020) ?
        @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent : null;
    if (chMask & 0x00040) elem.onmousemove   = (bits & 0x00040) ?
        @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent : null;
    if (chMask & 0x00080) elem.onkeydown     = (bits & 0x00080) ?
        @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent : null;
    if (chMask & 0x00100) elem.onkeypress    = (bits & 0x00100) ?
        @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent : null;
    if (chMask & 0x00200) elem.onkeyup       = (bits & 0x00200) ?
        @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent : null;
    if (chMask & 0x00400) elem.onchange      = (bits & 0x00400) ?
        @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent : null;
    if (chMask & 0x00800) elem.onfocus       = (bits & 0x00800) ?
        @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent : null;
    if (chMask & 0x01000) elem.onblur        = (bits & 0x01000) ?
        @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent : null;
    if (chMask & 0x02000) elem.onlosecapture = (bits & 0x02000) ?
        @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent : null;
    if (chMask & 0x04000) elem.onscroll      = (bits & 0x04000) ?
        @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent : null;
    if (chMask & 0x08000) elem.onload        = (bits & 0x08000) ?
        @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent : null;
    if (chMask & 0x10000) elem.onerror       = (bits & 0x10000) ?
        @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent : null;
    if (chMask & 0x20000) elem.onmousewheel  = (bits & 0x20000) ?
        @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent : null;
    if (chMask & 0x40000) elem.oncontextmenu = (bits & 0x40000) ?
        @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent : null;
    if (chMask & 0x80000) elem.onpaste       = (bits & 0x80000) ?
        @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent : null;

    // Handle drag and drop events.
    if (chMask & 0x1000000) {
        if (bits & 0x1000000) {
            elem.addEventListener("dragstart", @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent, true);
        } else {
            elem.removeEventListener("dragstart", @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent, true);
        }
    }
    if (chMask & 0x20000000) {
        if (bits & 0x20000000) {
            elem.addEventListener("dragend", @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent, true);
        } else {
            elem.removeEventListener("dragend", @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent, true);
        }
    }
    if (chMask & 0x2000000) {
        if (bits & 0x2000000) {
            elem.addEventListener("dragover", @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent, true);
        } else {
            elem.removeEventListener("dragover", @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent, true);
        }
    }
    if (chMask & 0x4000000) {
        if (bits & 0x4000000) {
            elem.addEventListener("dragenter", @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent, true);
        } else {
            elem.removeEventListener("dragenter", @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent, true);
        }
    }
    if (chMask & 0x8000000) {
        if (bits & 0x8000000) {
            elem.addEventListener("dragleave", @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent, true);
        } else {
            elem.removeEventListener("dragleave", @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent, true);
        }
    }
    if (chMask & 0x10000000) {
        if (bits & 0x10000000) {
            elem.addEventListener("drop", @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent, true);
        } else {
            elem.removeEventListener("drop", @com.google.gwt.user.client.impl.DOMImplStandard::dispatchEvent, true);
        }
    }
  }-*/;
}

//vim: ts=4 sw=4 expandtab