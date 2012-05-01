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

package org.mroy31.deejayd.mobile.animation;

import org.mroy31.deejayd.mobile.events.AnimationEndHandler;

import com.google.gwt.core.client.JavaScriptObject;
import com.google.gwt.dom.client.Element;

public class DeejaydAnimationUtils {

	/**
     * Adds a {@link AnimationEndEvent} handler.
     *
     * @param handler the handler
     * @return the callback for the event
     */
	public static native JavaScriptObject addAnimationEndHandler(Element ele, 
			AnimationEndHandler handler) /*-{
		var callback = function(){
		       handler.@org.mroy31.deejayd.mobile.events.AnimationEndHandler::onAnimationEnd()();
		}
	    if (navigator.userAgent.indexOf('MSIE') < 0) {  // no MSIE support
	       ele.addEventListener("webkitAnimationEnd", callback, false); // Webkit
	       ele.addEventListener("animationend", callback, false); // Mozilla
	    }
		return callback;
	}-*/;

	/**
     * Adds a {@link AnimationEndEvent} handler once.
     *
     * @param handler the handler
     */
	public static native void addAnimationEndHandlerOnce(Element ele, 
			AnimationEndHandler handler) /*-{
		var callback = function(e) {
			handler.@org.mroy31.deejayd.mobile.events.AnimationEndHandler::onAnimationEnd()();	
			
			ele.removeEventListener("webkitAnimationEnd", callback, false);
			ele.removeEventListener("animationend", callback, false);		
		};
		if (navigator.userAgent.indexOf('MSIE') < 0) {  // no MSIE support
	       ele.addEventListener("webkitAnimationEnd", callback, false); // Webkit
	       ele.addEventListener("animationend", callback, false); // Mozilla
	    }
	}-*/;

	public static native void removeAnimationEndHandler(Element ele, 
			JavaScriptObject callback) /*-{
		if (navigator.userAgent.indexOf('MSIE') < 0) {
	    	ele.removeEventListener("webkitAnimationEnd", callback, false);
	    	ele.addEventListener("animationend", callback, false);
		}  	
	}-*/; 
}

//vim: ts=4 sw=4 expandtab