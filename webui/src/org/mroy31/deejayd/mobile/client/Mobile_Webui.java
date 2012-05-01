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

package org.mroy31.deejayd.mobile.client;

import com.google.gwt.core.client.EntryPoint;
import com.google.gwt.core.client.GWT;
import com.google.gwt.core.client.RunAsyncCallback;
import com.google.gwt.dom.client.Element;
import com.google.gwt.resources.client.ClientBundle;
import com.google.gwt.resources.client.ImageResource;
import com.google.gwt.user.client.DOM;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.AbstractImagePrototype;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.RootPanel;

/**
 * Entry point classes define <code>onModuleLoad()</code>.
 */
public class Mobile_Webui implements EntryPoint {
	
	public static interface Resources extends ClientBundle {
		
		@Source("ui-loading.gif")
		ImageResource uiLoading();
	}

    /**
     * This is the entry point method.
     */
    public void onModuleLoad() {
    	Resources resources = GWT.create(Resources.class);
    	
        Element errorMsg = DOM.getElementById("errorMsg");
        errorMsg.removeFromParent();
        
        final FlowPanel loadingBox = new FlowPanel();
        loadingBox.addStyleName("loading-box");
        loadingBox.add(new HTML(AbstractImagePrototype.
    			create(resources.uiLoading()).getHTML()+"Loading ..."));       
        RootPanel.get().add(loadingBox);

        // split code to display load ui return as fast as possible
        GWT.runAsync(new RunAsyncCallback() {
        	public void onFailure(Throwable caught) {
                Window.alert("Code download failed");
              }

              public void onSuccess() {
            	  loadingBox.removeFromParent();
            	  
            	  MobileLayout panel = MobileLayout.getInstance();
                  RootPanel.get().add(panel);
              }
        });
    }
}

//vim: ts=4 sw=4 expandtab