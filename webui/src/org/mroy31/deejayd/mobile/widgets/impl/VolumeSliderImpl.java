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
 *
 * This Widget is mainly based on SLiderBar Widget from gwt-incubator project
 */

package org.mroy31.deejayd.mobile.widgets.impl;

import org.mroy31.deejayd.mobile.client.MobileLayout;
import org.mroy31.deejayd.mobile.widgets.VolumeSlider;

import com.google.gwt.event.dom.client.MouseDownEvent;
import com.google.gwt.event.dom.client.MouseDownHandler;
import com.google.gwt.event.dom.client.MouseMoveEvent;
import com.google.gwt.event.dom.client.MouseMoveHandler;
import com.google.gwt.event.dom.client.MouseUpEvent;
import com.google.gwt.event.dom.client.MouseUpHandler;
import com.google.gwt.user.client.DOM;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Widget;

public class VolumeSliderImpl {
    protected final MobileLayout ui = MobileLayout.getInstance();
    protected boolean sliding = false;
    protected VolumeSlider volSlider;
    private Image knob = new Image(ui.resources.slider());

    public Widget getKnob() {
        return knob;
    }

    public void load(VolumeSlider volS) {
        volSlider = volS;
        knob.addStyleName(ui.resources.mobileCss().volHandle());

        // set touch events
        knob.addMouseDownHandler(new MouseDownHandler() {
            public void onMouseDown(MouseDownEvent event) {
                sliding = true;
                DOM.setCapture(knob.getElement());
                event.preventDefault();
            }
        });
        knob.addMouseMoveHandler(new MouseMoveHandler() {
            public void onMouseMove(MouseMoveEvent event) {
                if (sliding) {
                    int x = event.getClientX();
                    volSlider.slideToX(x);
                }
            }
        });
        knob.addMouseUpHandler(new MouseUpHandler() {
            public void onMouseUp(MouseUpEvent event) {
                if (sliding) {
                    DOM.releaseCapture(knob.getElement());
                    int x = event.getClientX();
                    volSlider.slideToX(x);
                    sliding = false;
                }
            }
        });
    }
}

//vim: ts=4 sw=4 expandtab