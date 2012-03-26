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

package org.mroy31.deejayd.mobile.events;


import com.google.gwt.event.dom.client.TouchCancelHandler;
import com.google.gwt.event.dom.client.TouchEndEvent;
import com.google.gwt.event.dom.client.TouchEndHandler;
import com.google.gwt.event.dom.client.TouchMoveEvent;
import com.google.gwt.event.dom.client.TouchMoveHandler;
import com.google.gwt.event.dom.client.TouchStartEvent;
import com.google.gwt.event.dom.client.TouchStartHandler;
import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.event.shared.HasHandlers;

public interface HasTouchHandlers extends HasHandlers {
     /**
       * Adds a {@link TouchStartEvent} handler.
       *
       * @param handler the handler
       * @return the registration for the event
       */
      HandlerRegistration addTouchStartHandler(TouchStartHandler handler);

      /**
       * Adds a {@link TouchCancelEvent} handler.
       *
       * @param handler the handler
       * @return the registration for the event
       */
      HandlerRegistration addTouchCancelHandler(TouchCancelHandler handler);
      
      /**
       * Adds a {@link TouchMoveEvent} handler.
       *
       * @param handler the handler
       * @return the registration for the event
       */
      HandlerRegistration addTouchMoveHandler(TouchMoveHandler handler);

      /**
       * Adds a {@link TouchEndEvent} handler.
       *
       * @param handler the handler
       * @return the registration for the event
       */
      HandlerRegistration addTouchEndHandler(TouchEndHandler handler);
}

//vim: ts=4 sw=4 expandtab