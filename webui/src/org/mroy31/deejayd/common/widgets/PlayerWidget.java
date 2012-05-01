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

package org.mroy31.deejayd.common.widgets;

import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.uibinder.client.UiHandler;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.ui.Composite;

public abstract class PlayerWidget extends Composite {
    protected final DeejaydUIWidget privateUI;

    protected abstract class AbstractRpcTimer extends Timer {
    	boolean updatePending = false;
    	boolean updateRunning = false;
    	
    	int TIMER = 600;
        int value;       
        AnswerHandler<Boolean> handler = new AnswerHandler<Boolean>() {
			
			@Override
			public void onAnswer(Boolean answer) {
				updateRunning = false;
				if (!updatePending) {
					GWT.log("No update pending, update UI");
					privateUI.update();
				}
					
			}
		};
        
        public void updateValue(int value) {
        	GWT.log("update timer value : "+Integer.toString(value));
        	// cancel old timer
        	if (this.updatePending) {
        		GWT.log("update pending cancel timer");
        		this.cancel();
        	}
        	
        	this.value = value;
        	this.updatePending = true;
        	this.schedule(TIMER);
        }
    }
    
    protected class SeekTimer extends AbstractRpcTimer {
    	        
        @Override
        public void run() {
        	GWT.log("Run seek command");
        	
        	updateRunning = true; updatePending = false;
            privateUI.rpc.seek(value, handler);
        }
                
    }
    protected SeekTimer seekTimer = new SeekTimer();

    protected class VolumeTimer extends AbstractRpcTimer {

        @Override
        public void run() {
        	updateRunning = true; updatePending = false;
            privateUI.rpc.setVolume(value, handler);
        }
        
    }
    protected VolumeTimer volumeTimer = new VolumeTimer();

    public PlayerWidget(DeejaydUIWidget ui) {
        this.privateUI = ui;
    }

    @UiHandler("playToggleButton")
    public void playButtonHandler(ClickEvent event) {
        privateUI.rpc.playToggle();
    }

    @UiHandler("stopButton")
    public void stopButtonHandler(ClickEvent event) {
        privateUI.rpc.stop();
    }

    @UiHandler("nextButton")
    public void nextButtonHandler(ClickEvent event) {
        privateUI.rpc.next();
    }

    @UiHandler("previousButton")
    public void previousButtonHandler(ClickEvent event) {
        privateUI.rpc.previous();
    }
}

//vim: ts=4 sw=4 expandtab