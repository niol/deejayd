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

import com.google.gwt.user.client.DOM;
import com.google.gwt.user.client.ui.HasHTML;
import com.google.gwt.user.client.ui.HasText;
import com.google.gwt.user.client.ui.Widget;

/**
 * A Label/HTML replacement that does not sink events. By default, the standard
 * Label and HTML widgets call sinkEvents() in their constructors. On the
 * iPhone, this causes the browser to render these elements with a dark
 * background and display an "action bubble" when the user performs a
 * tap-and-hold gesture on these elements. The UnsunkLabel exists to replace the
 * basic functions of Label and HTML without adding this unwanted UI behavior.
 */
public class UnsunkLabel extends Widget implements HasText, HasHTML {

    public UnsunkLabel() {
        setElement(DOM.createDiv());
    }

    public UnsunkLabel(String contents) {
        this();
        setText(contents);
    }

    public UnsunkLabel(String contents, boolean asHTML) {
        this();
        if (asHTML) {
            setHTML(contents);
        } else {
            setText(contents);
        }
    }

    public String getHTML() {
        return DOM.getInnerHTML(getElement());
    }

    public String getText() {
        return DOM.getInnerText(getElement());
    }

    public void setHTML(String html) {
        DOM.setInnerHTML(getElement(), html);
    }

    public void setText(String text) {
        DOM.setInnerText(getElement(), text);
    }
}

//vim: ts=4 sw=4 expandtab