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

import org.mroy31.deejayd.mobile.client.MobileLayout;
import org.mroy31.deejayd.mobile.widgets.impl.VolumeSliderImpl;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.HasValueChangeHandlers;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.user.client.DOM;
import com.google.gwt.user.client.Element;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Widget;

public class VolumeSlider extends Composite
        implements ClickHandler, HasValueChangeHandlers<Integer> {
    protected final MobileLayout ui = MobileLayout.getInstance();

    private double maxValue = 100;
    private double minValue = 0;
    private double stepSize = 5;
    private double curValue = -1;

    private VolumeSliderImpl knobImpl = GWT.create(VolumeSliderImpl.class);
    private Widget slider;
    private FlowPanel sliderBar = new FlowPanel();
    private Image volDown = new Image(ui.resources.volDown());
    private Image volUp = new Image(ui.resources.volUp());

    public VolumeSlider() {
        knobImpl.load(this);

        HorizontalPanel panel = new HorizontalPanel();
        panel.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);
        panel.setHorizontalAlignment(HorizontalPanel.ALIGN_CENTER);
        panel.setWidth("100%");

        volDown.addClickHandler(this);
        volUp.addClickHandler(this);

        FlowPanel sliderPanel = new FlowPanel();
        sliderPanel.addStyleName(ui.resources.mobileCss().volSliderPanel());
        slider = knobImpl.getKnob();
        sliderBar.addStyleName(ui.resources.mobileCss().volSlider());
        sliderBar.add(slider);
        sliderPanel.add(sliderBar);

        panel.add(volDown);
        panel.setCellWidth(volDown, Integer.toString(volDown.getWidth())+"px");
        panel.add(sliderPanel);
        panel.add(volUp);
        panel.setCellWidth(volUp, Integer.toString(volUp.getWidth())+"px");

        initWidget(panel);
        addStyleName(ui.resources.mobileCss().volPanel());
    }

    public void onClick(ClickEvent event) {
        Widget sender = (Widget) event.getSource();
        if (sender == volDown) {
            setCurrentValue((int) (curValue-stepSize), true);
        } else if (sender == volUp) {
            setCurrentValue((int) (curValue+stepSize), true);
        }
    }

    public HandlerRegistration addValueChangeHandler(
            ValueChangeHandler<Integer> handler) {
        return addHandler(handler, ValueChangeEvent.getType());
    }

    /**
     * Return the current value.
     *
     * @return the current value
     */
    public double getCurrentValue() {
        return curValue;
    }

    /**
     * Return the total range between the minimum and maximum values.
     *
     * @return the total range
     */
    public double getTotalRange() {
        if (minValue > maxValue) {
            return 0;
        } else {
            return maxValue - minValue;
        }
    }

    public void setCurrentValue(int value, Boolean fireEvent) {
        double oldValue = this.curValue;
        this.curValue = Math.max(minValue, Math.min(maxValue, value));

        if (this.curValue != oldValue) {
            // Redraw the knob
            drawKnob();

            // Fire the onValueChange event
            if (fireEvent) {
                ValueChangeEvent.fire(this, (int)this.curValue);
            }
        }
    }

    public void slideToX(int x) {
        if (x > 0) {
            Element lineElement = sliderBar.getElement();
            int lineWidth = DOM.getElementPropertyInt(lineElement,
                    "offsetWidth");
            int lineLeft = DOM.getAbsoluteLeft(lineElement);
            double percent = (double) (x - lineLeft) / lineWidth * 1.0;
            setCurrentValue((int)((getTotalRange() * percent)+ minValue), true);
        }
    }

    /**
     * This method is called when the dimensions of the parent element change.
     * Subclasses should override this method as needed.
     *
     * @param width the new client width of the element
     * @param height the new client height of the element
     */
    public void onResize(int width, int height) {
        drawKnob();
    }

    /**
     * Redraw the progress bar when something changes the layout.
     */
    public void redraw() {
        if (isAttached()) {
            int width = DOM.getElementPropertyInt(getElement(), "clientWidth");
            int height = DOM.getElementPropertyInt(getElement(),"clientHeight");
            onResize(width, height);
        }
    }

    /**
     * Get the percentage of the knob's position relative to the size
     * of the line.
     * The return value will be between 0.0 and 1.0.
     *
     * @return the current percent complete
     */
    protected double getKnobPercent() {
        // If we have no range
        if (maxValue <= minValue) {
            return 0;
        }

        // Calculate the relative progress
        double percent = (curValue - minValue) / (maxValue - minValue);
        return Math.max(0.0, Math.min(1.0, percent));
    }

    /**
     * Draw the knob where it is supposed to be relative to the line.
     */
    public void drawKnob() {
        // Move the knob to the correct position
        int lineWidth = sliderBar.getOffsetWidth();
        int knobWidth = slider.getOffsetWidth();
        int knobLeftOffset = (int) (getKnobPercent() * lineWidth)
                - (knobWidth / 2);
        knobLeftOffset = Math.min(knobLeftOffset, lineWidth-(knobWidth/2)-1);
        DOM.setStyleAttribute(slider.getElement(), "left", knobLeftOffset+"px");
    }
}

//vim: ts=4 sw=4 expandtab