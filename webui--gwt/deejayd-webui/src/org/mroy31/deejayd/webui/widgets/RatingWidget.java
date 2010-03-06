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

package org.mroy31.deejayd.webui.widgets;

import java.util.HashMap;

import org.mroy31.deejayd.webui.resources.WebuiResources;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.HasValueChangeHandlers;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.user.client.DOM;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.HasValue;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Widget;

public class RatingWidget extends Composite implements ClickHandler,
        HasValueChangeHandlers<Integer>, HasValue<Integer> {

    private int currentValue;
    private HashMap<Integer,Image> ratingImages = new HashMap<Integer,Image>();

    /**
     * Create a rating widget.
     */
    public RatingWidget(int value, WebuiResources resources) {
        currentValue = value;

        FlowPanel panel = new FlowPanel();
        for (int i=0; i<4; i++) {
            Image img = new Image(resources.star());
            img.addClickHandler(this);
            if (i >= currentValue) {
                DOM.setStyleAttribute(img.getElement(), "opacity", "0.4");
            }
            ratingImages.put(i, img);
            panel.add(img);
        }

        initWidget(panel);
        DOM.setStyleAttribute(getElement(), "display", "inline-block");
    }

    @Override
    public void onClick(ClickEvent event) {
        Widget sender = (Widget) event.getSource();
        for (int i=0; i<4; i++) {
            if (sender == ratingImages.get(i)) {
                setValue(i+1, true);
                break;
            }
        }

    }

    @Override
    public HandlerRegistration addValueChangeHandler(
            ValueChangeHandler<Integer> handler) {
        return addHandler(handler, ValueChangeEvent.getType());
    }

    @Override
    public Integer getValue() {
        return currentValue;
    }

    @Override
    public void setValue(Integer value) {
        setValue(value, true);

    }

    @Override
    public void setValue(Integer value, boolean fireEvents) {
        if (currentValue != value) {
            for (int i=0; i<4; i++) {
                String opacity = "1.0";
                if (i >= value) {
                    opacity = "0.4";
                }
                DOM.setStyleAttribute(ratingImages.get(i).getElement(),
                        "opacity", opacity);
            }
            currentValue = value;
            if (fireEvents) {
                ValueChangeEvent.fire(this, currentValue);
            }
        }
    }
}

//vim: ts=4 sw=4 expandtab