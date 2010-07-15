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

import org.mroy31.deejayd.mobile.events.HasTouchHandlers;
import org.mroy31.deejayd.mobile.events.TouchEndEvent;
import org.mroy31.deejayd.mobile.events.TouchEndHandler;
import org.mroy31.deejayd.mobile.events.TouchMoveEvent;
import org.mroy31.deejayd.mobile.events.TouchMoveHandler;
import org.mroy31.deejayd.mobile.events.TouchStartEvent;
import org.mroy31.deejayd.mobile.events.TouchStartHandler;
import org.mroy31.deejayd.mobile.widgets.VolumeSlider;

import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.user.client.DOM;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Widget;

public class VolumeSliderMobileImpl extends VolumeSliderImpl {
    private class Knob extends Composite implements HasTouchHandlers {

        public Knob() {
            Image img = new Image(ui.resources.slider());

            initWidget(img);
            addStyleName(ui.resources.mobileCss().volHandle());
        }

        @Override
        public HandlerRegistration addTouchEndHandler(TouchEndHandler handler) {
            return addDomHandler(handler, TouchEndEvent.getType());
        }

        @Override
        public HandlerRegistration addTouchMoveHandler(
                TouchMoveHandler handler) {
            return addDomHandler(handler, TouchMoveEvent.getType());
        }

        @Override
        public HandlerRegistration addTouchStartHandler(
                TouchStartHandler handler) {
            return addDomHandler(handler, TouchStartEvent.getType());
        }

    }
    private Knob knob = new Knob();

    public Widget getKnob() {
        return knob;
    }

    public void load(VolumeSlider volS) {
        volSlider = volS;

        // set touch events
        knob.addTouchStartHandler(new TouchStartHandler() {
            @Override
            public void onTouchStart(TouchStartEvent event) {
                sliding = true;
                DOM.setCapture(knob.getElement());
                event.preventDefault();
            }
        });
        knob.addTouchMoveHandler(new TouchMoveHandler() {
            @Override
            public void onTouchMove(TouchMoveEvent event) {
                if (sliding) {
                    int x = event.touches().get(0).pageX();
                    volSlider.slideToX(x);
                }
            }
        });
        knob.addTouchEndHandler(new TouchEndHandler() {
            @Override
            public void onTouchEnd(TouchEndEvent event) {
                if (sliding) {
                    DOM.releaseCapture(knob.getElement());
                    sliding = false;
                }
            }
        });
    }
}

//vim: ts=4 sw=4 expandtab