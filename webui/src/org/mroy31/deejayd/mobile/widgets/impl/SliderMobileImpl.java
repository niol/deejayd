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
 * This Widget is mainly based on SpinnerValue from gwt-incubator project
 */

package org.mroy31.deejayd.mobile.widgets.impl;

import org.mroy31.deejayd.mobile.widgets.Slider;
import org.mroy31.deejayd.mobile.widgets.Slider.SliderHandle;

import com.google.gwt.event.dom.client.TouchEndEvent;
import com.google.gwt.event.dom.client.TouchEndHandler;
import com.google.gwt.event.dom.client.TouchMoveEvent;
import com.google.gwt.event.dom.client.TouchMoveHandler;
import com.google.gwt.event.dom.client.TouchStartEvent;
import com.google.gwt.event.dom.client.TouchStartHandler;
import com.google.gwt.user.client.DOM;

public class SliderMobileImpl extends SliderImpl {

	public void loadEvents(final Slider slider) {
		final SliderHandle handle = slider.getHandle();
		
		handle.addTouchStartHandler(new TouchStartHandler() {
			
			@Override
			public void onTouchStart(TouchStartEvent event) {
				sliding = true;
                DOM.setCapture(handle.getElement());
                event.preventDefault();
			}
		});
		
		handle.addTouchMoveHandler(new TouchMoveHandler() {
			
			@Override
			public void onTouchMove(TouchMoveEvent event) {
				if (sliding) {
                    int x = event.getTouches().get(0).getPageX();
                    slider.slideToX(x);
                }
			}
		});
		
		handle.addTouchEndHandler(new TouchEndHandler() {
			
			@Override
			public void onTouchEnd(TouchEndEvent event) {
				if (sliding) {
                    DOM.releaseCapture(handle.getElement());
                    int x = event.getTouches().get(0).getPageX();
                    slider.slideToX(x);
                    sliding = false;
                    slider.fireChangeEndEvent();
                }
			}
		});
	}
}

//vim: ts=4 sw=4 expandtab