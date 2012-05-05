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
 *
 */

package org.mroy31.deejayd.mobile.widgets;

import org.mroy31.deejayd.mobile.client.MobileLayout;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.HasValue;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.google.gwt.user.client.ui.Widget;

public class SpinnerValue extends Composite implements HasValue<Integer>, ClickHandler {
	private final MobileLayout ui = MobileLayout.getInstance();

	int value = 0;
	
	int maxValue = 100;
	int minValue = 0;
	int stepSize = 1;
	
	Image firstArrow = new Image(ui.resources.downArrow());
	Image lastArrow = new Image(ui.resources.upArrow());
	Label label = new Label("0");
	
	public SpinnerValue() {
		this(false);
	}
	
	public SpinnerValue(boolean inline) {		
		if (inline) {
			HorizontalPanel panel = new HorizontalPanel();
			panel.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);
			
			firstArrow = new Image(ui.resources.leftArrow());
			lastArrow = new Image(ui.resources.rightArrow());
			
			panel.add(firstArrow);
			panel.add(label);
			panel.add(lastArrow);
			initWidget(panel);
		} else {
			VerticalPanel panel = new VerticalPanel();
			panel.setHorizontalAlignment(VerticalPanel.ALIGN_CENTER);
			
			panel.add(lastArrow);
			panel.add(label);
			panel.add(firstArrow);
			initWidget(panel);
		}
		
		firstArrow.addClickHandler(this);
		lastArrow.addClickHandler(this);	
		addStyleName(ui.resources.mobileCss().spinnerValue());
	}

	public int getMaxValue() {
		return maxValue;
	}
	
	public void setMaxValue(int maxValue) {
		this.maxValue = maxValue;
	}
	
	public int getMinValue() {
		return minValue;
	}

	public void setMinValue(int minValue) {
		this.minValue = minValue;
	}

	public int getStepSize() {
		return stepSize;
	}
	
	public void setStepSize(int stepSize) {
		this.stepSize = stepSize;
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
		value = Math.min(maxValue, Math.max(minValue, value));
		if (value != this.value) {
			this.value = value;
			label.setText(Integer.toString(value));
			
			if (fireEvents) {
	            ValueChangeEvent.fire(this, this.value);
	        }
		}
	}

	@Override
	public void onClick(ClickEvent event) {
		Widget sender = (Widget) event.getSource();
		if (sender == firstArrow) {
			int v = value-stepSize;
			if (value == minValue) {
				v = maxValue;
			}
			setValue(v, true);
		} else if (sender == lastArrow) {
			int v = value+stepSize;
			if (value == maxValue) {
				v = minValue;
			}
			setValue(v, true);
		}
	}
}

//vim: ts=4 sw=4 expandtab