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
import org.mroy31.deejayd.mobile.widgets.impl.SliderImpl;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.dom.client.HasAllMouseHandlers;
import com.google.gwt.event.dom.client.HasAllTouchHandlers;
import com.google.gwt.event.dom.client.HasClickHandlers;
import com.google.gwt.event.dom.client.MouseDownEvent;
import com.google.gwt.event.dom.client.MouseDownHandler;
import com.google.gwt.event.dom.client.MouseMoveEvent;
import com.google.gwt.event.dom.client.MouseMoveHandler;
import com.google.gwt.event.dom.client.MouseOutEvent;
import com.google.gwt.event.dom.client.MouseOutHandler;
import com.google.gwt.event.dom.client.MouseOverEvent;
import com.google.gwt.event.dom.client.MouseOverHandler;
import com.google.gwt.event.dom.client.MouseUpEvent;
import com.google.gwt.event.dom.client.MouseUpHandler;
import com.google.gwt.event.dom.client.MouseWheelEvent;
import com.google.gwt.event.dom.client.MouseWheelHandler;
import com.google.gwt.event.dom.client.TouchCancelEvent;
import com.google.gwt.event.dom.client.TouchCancelHandler;
import com.google.gwt.event.dom.client.TouchEndEvent;
import com.google.gwt.event.dom.client.TouchEndHandler;
import com.google.gwt.event.dom.client.TouchMoveEvent;
import com.google.gwt.event.dom.client.TouchMoveHandler;
import com.google.gwt.event.dom.client.TouchStartEvent;
import com.google.gwt.event.dom.client.TouchStartHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.event.shared.EventHandler;
import com.google.gwt.event.shared.GwtEvent;
import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.user.client.DOM;
import com.google.gwt.user.client.ui.HasValue;
import com.google.gwt.user.client.ui.SimplePanel;
import com.google.gwt.user.client.ui.Widget;

public class Slider extends SimplePanel implements 
		HasClickHandlers, HasValue<Integer> {
	private final MobileLayout ui = MobileLayout.getInstance();
	
	/**
	 * Virtual event and handler to know when slider stop to change
	 * this event fire when the mouseUpEvent/touchEndEvent appears
	 * @author roy
	 *
	 */
	public interface ChangeEndHandler extends EventHandler {
		public void onChangeEnd();
	}	
	public static class ChangeEndEvent extends GwtEvent<ChangeEndHandler> {
		public static final Type<ChangeEndHandler> TYPE = new Type<ChangeEndHandler>();

		@Override
		public com.google.gwt.event.shared.GwtEvent.Type<ChangeEndHandler> getAssociatedType() {
			return TYPE;
		}

		public static Type<ChangeEndHandler> getType() {
	        return TYPE;
	    }
		
		@Override
		protected void dispatch(ChangeEndHandler handler) {
			handler.onChangeEnd();
		}
	}
	
	/**
	 * Slider handle
	 * Widget definition
	 * @author roy
	 *
	 */
	public class SliderHandle extends Widget 
			implements HasAllMouseHandlers, HasAllTouchHandlers {
		
		public SliderHandle() {
			setElement(DOM.createAnchor());
			getElement().appendChild(DOM.createSpan());
		}
		
		public void setPosition(double percent) {
			String value = Double.toString(percent) + "%";
			DOM.setStyleAttribute(getElement(), "left", value);
		}

		@Override
		public HandlerRegistration addMouseDownHandler(MouseDownHandler handler) {
			return addDomHandler(handler, MouseDownEvent.getType());
		}

		@Override
		public HandlerRegistration addMouseUpHandler(MouseUpHandler handler) {
			return addDomHandler(handler, MouseUpEvent.getType());
		}

		@Override
		public HandlerRegistration addMouseOutHandler(MouseOutHandler handler) {
			return addDomHandler(handler, MouseOutEvent.getType());
		}

		@Override
		public HandlerRegistration addMouseOverHandler(MouseOverHandler handler) {
			return addDomHandler(handler, MouseOverEvent.getType());
		}

		@Override
		public HandlerRegistration addMouseMoveHandler(MouseMoveHandler handler) {
			return addDomHandler(handler, MouseMoveEvent.getType());
		}

		@Override
		public HandlerRegistration addMouseWheelHandler(
				MouseWheelHandler handler) {
			return addDomHandler(handler, MouseWheelEvent.getType());
		}

		@Override
		public HandlerRegistration addTouchCancelHandler(TouchCancelHandler handler) {
		    return addDomHandler(handler, TouchCancelEvent.getType());
		}

		@Override
		public HandlerRegistration addTouchEndHandler(TouchEndHandler handler) {
		    return addDomHandler(handler, TouchEndEvent.getType());
		}

		@Override
		public HandlerRegistration addTouchMoveHandler(TouchMoveHandler handler) {
		    return addDomHandler(handler, TouchMoveEvent.getType());
		}

		@Override
		public HandlerRegistration addTouchStartHandler(TouchStartHandler handler) {
		    return addDomHandler(handler, TouchStartEvent.getType());
		}
	}
	private SliderHandle handle = new SliderHandle();
	
	/**
	 * Slider value
	 */
	private int value = 0;
	
	 /**
     * The maximum slider value.
     */
	private int maxValue = 100;
	
	/**
     * The minimum slider value.
     */
	private int minValue = 0;
	
	SliderImpl impl = GWT.create(SliderImpl.class);
	private final MobileResources.MobileCss style = ui.resources.mobileCss();
	
	public Slider() {
		super(DOM.createDiv());
		
		// add handle
		add(handle);
		
		addClickHandler(new ClickHandler() {
			
			@Override
			public void onClick(ClickEvent event) {
				int x = event.getClientX();
				slideToX(x);
			}
		});
		impl.loadEvents(this);
		
		// setStyle
		addStyleName(this.style.slider());
		handle.addStyleName(this.style.sliderHandle());
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
    
	public void slideToX(int x) {
		int sliderWidth = getOffsetWidth();
		int sliderLeftPos = getAbsoluteLeft();
		
		double percent = (double) (x - sliderLeftPos) / sliderWidth * 1.0;
		setValue((int)((getTotalRange() * percent)+ minValue), true);
	}
	
	public SliderHandle getHandle() {
		return handle;
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
		if (this.value != value) {
			this.value = value;
			
			// update the handle position
			double percent = (double) value / (double) getTotalRange();
			handle.setPosition(percent*100.0);
	
			// Fire the onValueChange event
	        if (fireEvents) {
	            ValueChangeEvent.fire(this,  this.value);
	        }
		}
	}
	
	@Override
	public HandlerRegistration addClickHandler(ClickHandler handler) {
		return addDomHandler(handler, ClickEvent.getType());
	}

	@Override
	public HandlerRegistration addValueChangeHandler(
			ValueChangeHandler<Integer> handler) {
		return addHandler(handler, ValueChangeEvent.getType());
	}

	public void fireChangeEndEvent() {
		fireEvent(new ChangeEndEvent());
	}
	
	public HandlerRegistration addChangeEndHandler(
			ChangeEndHandler handler) {
		return addHandler(handler, ChangeEndEvent.getType());
	}
}

//vim: ts=4 sw=4 expandtab