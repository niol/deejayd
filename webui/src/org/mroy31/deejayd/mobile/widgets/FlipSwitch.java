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
import org.mroy31.deejayd.mobile.resources.MobileResources;
import org.mroy31.deejayd.mobile.widgets.Slider.ChangeEndHandler;

import com.google.gwt.core.client.Scheduler;
import com.google.gwt.core.client.Scheduler.ScheduledCommand;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.HasValue;
import com.google.gwt.user.client.ui.Label;

public class FlipSwitch extends Composite implements HasValue<Boolean>, ClickHandler {
	private final MobileLayout ui = MobileLayout.getInstance();
	private boolean value;

	Label onElt = new Label();
	Label offElt = new Label();
	Slider slider = new Slider();

	private final MobileResources.MobileCss style = ui.resources.mobileCss();
	
	public FlipSwitch() {
		FlowPanel panel = new FlowPanel();
		panel.addStyleName(this.style.flipSwitch());	
		initWidget(panel);
		
	    onElt.setText(ui.i18nConst.on());
	    onElt.addStyleName(this.style.flipSwitchElt() 
	    		+ " " + this.style.flipSwitchOnElt());
	    onElt.addClickHandler(this);
	    panel.add(onElt);
		
	    offElt.setText(ui.i18nConst.off());
	    offElt.addStyleName(this.style.flipSwitchElt() 
	    		+ " " + this.style.flipSwitchOffElt());
	    offElt.addClickHandler(this);
	    panel.add(offElt);
	    
	    panel.add(slider);
	    slider.addValueChangeHandler(new ValueChangeHandler<Integer>() {

			@Override
			public void onValueChange(ValueChangeEvent<Integer> event) {
				int sliderLeft = getWidget().getAbsoluteLeft();
				int sliderWidth = slider.getOffsetWidth();
				int handleWidth = slider.getHandle().getOffsetWidth();
				int handleLeft = slider.getHandle().getAbsoluteLeft();
				
				double onEltWidth =  (handleLeft+handleWidth-sliderLeft);
				double offEltWidth = (sliderLeft+sliderWidth+handleWidth-handleLeft);
				
				onElt.setWidth(Double.toString(onEltWidth)+"px");
				offElt.setWidth(Double.toString(offEltWidth)+"px");
			}
		});
	    slider.addChangeEndHandler(new ChangeEndHandler() {
			
			@Override
			public void onChangeEnd() {
				Scheduler.get().scheduleDeferred(new ScheduledCommand() {
					
					@Override
					public void execute() {
						setValue(slider.getValue() > 50);
					}
				});
			}
		});
	}
	
	@Override
	public HandlerRegistration addValueChangeHandler(
			ValueChangeHandler<Boolean> handler) {
		return addHandler(handler, ValueChangeEvent.getType());
	}

	@Override
	public Boolean getValue() {
		return value;
	}

	@Override
	public void setValue(Boolean value) {
		setValue(value, false);
	}

	@Override
	public void setValue(Boolean value, boolean fireEvents) {
		if (this.value != value) {
			this.value = value;
	
			// Fire the onValueChange event
	        if (fireEvents) {
	            ValueChangeEvent.fire(this,  this.value);
	        }
		}
		redraw();
	}

	@Override
	public void onClick(ClickEvent event) {
		this.setValue(!this.value, true);
	}

	private void redraw() {
		int sliderPos = 0; int offWidth = 100; int onWidth = 0;
		if (value) {
			sliderPos = 100; offWidth = 0; onWidth = 100;
		}
		onElt.setWidth(Integer.toString(onWidth)+"%");
		offElt.setWidth(Integer.toString(offWidth)+"%");
		slider.setValue(sliderPos);
	}
}

//vim: ts=4 sw=4 expandtab