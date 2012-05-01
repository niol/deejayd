/*
 * Deejayd, a media player daemon
 * Copyright (C) 2007-2012 Mickael Royer <mickael.royer@gmail.com>
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

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.HasValue;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Widget;

public class VolumeControl extends Composite
        implements ClickHandler, HasValue<Integer> {
    protected final MobileLayout ui = MobileLayout.getInstance();

    private int maxValue = 100;
    private int minValue = 0;
    private int stepSize = 5;
    private int value = 0;

    private Slider slider = new Slider();
    private Image volDown = new Image(ui.resources.volDown());
    private Image volUp = new Image(ui.resources.volUp());

    public VolumeControl() {
        HorizontalPanel panel = new HorizontalPanel();
        panel.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);
        panel.setHorizontalAlignment(HorizontalPanel.ALIGN_CENTER);
        panel.setWidth("100%");

        volDown.addClickHandler(this);
        volUp.addClickHandler(this);

        FlowPanel sliderPanel = new FlowPanel();
        sliderPanel.add(slider);

        panel.add(volDown);
        panel.setCellWidth(volDown, Integer.toString(volDown.getWidth())+"px");
        panel.add(sliderPanel);
        panel.add(volUp);
        panel.setCellWidth(volUp, Integer.toString(volUp.getWidth())+"px");

        initWidget(panel);
        addStyleName(ui.resources.mobileCss().volPanel());
        slider.addValueChangeHandler(new ValueChangeHandler<Integer>() {

			@Override
			public void onValueChange(ValueChangeEvent<Integer> event) {
				setValue(event.getValue(), true);
			}
		});
    }

    public void onClick(ClickEvent event) {
        Widget sender = (Widget) event.getSource();
        if (sender == volDown) {
            setValue((int) (value-stepSize), true);
        } else if (sender == volUp) {
            setValue((int) (value+stepSize), true);
        }
    }

    @Override
    public HandlerRegistration addValueChangeHandler(
            ValueChangeHandler<Integer> handler) {
        return addHandler(handler, ValueChangeEvent.getType());
    }

    @Override
	public Integer getValue() {
		return value;
	}

	@Override
	public void setValue(Integer value) {
		setValue(value, false);
	}

	@Override
	public void setValue(Integer value, boolean fireEvents) {
		value = Math.max(minValue, Math.min(maxValue, value));
		
		if (this.value != value) {
			this.value = value;
			slider.setValue(value);
			
			// Fire the onValueChange event
            if (fireEvents) {
                ValueChangeEvent.fire(this, (int)this.value);
            }
		}
	}

}

//vim: ts=4 sw=4 expandtab