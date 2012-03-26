package org.mroy31.deejayd.mobile.events;

import com.google.gwt.core.client.JavaScriptObject;
import com.google.gwt.dom.client.Element;

public class DeejaydEventsUtils {

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
