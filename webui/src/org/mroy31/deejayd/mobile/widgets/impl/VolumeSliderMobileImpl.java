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
import org.mroy31.deejayd.mobile.widgets.VolumeSlider;

import com.google.gwt.event.dom.client.TouchCancelEvent;
import com.google.gwt.event.dom.client.TouchCancelHandler;
import com.google.gwt.event.dom.client.TouchEndEvent;
import com.google.gwt.event.dom.client.TouchEndHandler;
import com.google.gwt.event.dom.client.TouchMoveEvent;
import com.google.gwt.event.dom.client.TouchMoveHandler;
import com.google.gwt.event.dom.client.TouchStartEvent;
import com.google.gwt.event.dom.client.TouchStartHandler;
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

        public HandlerRegistration addTouchEndHandler(TouchEndHandler handler) {
            return addDomHandler(handler, TouchEndEvent.getType());
        }

        public HandlerRegistration addTouchMoveHandler(
                TouchMoveHandler handler) {
            return addDomHandler(handler, TouchMoveEvent.getType());
        }

        public HandlerRegistration addTouchStartHandler(
                TouchStartHandler handler) {
            return addDomHandler(handler, TouchStartEvent.getType());
        }
        
        public HandlerRegistration addTouchCancelHandler(
                TouchCancelHandler handler) {
            return addDomHandler(handler, TouchCancelEvent.getType());
        }

    }
    private Knob knob = new Knob();

    @Override
    public Widget getKnob() {
        return knob;
    }

    @Override
    public void load(VolumeSlider volS) {
        volSlider = volS;

        // set touch events
        knob.addTouchStartHandler(new TouchStartHandler() {
            public void onTouchStart(TouchStartEvent event) {
                sliding = true;
                DOM.setCapture(knob.getElement());
                event.preventDefault();
            }
        });
        knob.addTouchMoveHandler(new TouchMoveHandler() {
            public void onTouchMove(TouchMoveEvent event) {
                if (sliding) {
                    int x = event.getTouches().get(0).getPageX();
                    volSlider.slideToX(x);
                }
            }
        });
        knob.addTouchEndHandler(new TouchEndHandler() {
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