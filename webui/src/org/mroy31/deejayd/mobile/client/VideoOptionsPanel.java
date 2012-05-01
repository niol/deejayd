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

import java.util.HashMap;

import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.mobile.widgets.SpinnerValue;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ChangeEvent;
import com.google.gwt.event.dom.client.ChangeHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiFactory;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.ListBox;
import com.google.gwt.user.client.ui.Widget;

public class VideoOptionsPanel extends Composite implements ChangeHandler {
	private final MobileLayout ui = MobileLayout.getInstance();

	private static VideoOptionsPanelUiBinder uiBinder = GWT
			.create(VideoOptionsPanelUiBinder.class);

	interface VideoOptionsPanelUiBinder extends
			UiBinder<Widget, VideoOptionsPanel> {
	}
	
	boolean hasZoom;
	@UiField HorizontalPanel zoomPanel;
	@UiField Label zoomLabel;
	@UiField SpinnerValue zoomValue;
	
	boolean hasAspectRatio;
	@UiField HorizontalPanel aspectRatioPanel;
	@UiField Label aspectRatioLabel;
	@UiField ListBox aspectRatio;
	
	@UiField HorizontalPanel audioChannelPanel;
	@UiField Label audioChannelLabel;
	@UiField ListBox audioChannel;
	
	@UiField HorizontalPanel subChannelPanel;
	@UiField Label subChannelLabel;
	@UiField ListBox subChannel;
	
	boolean hasSubOffset;
	@UiField HorizontalPanel subOffsetPanel;
	@UiField Label subOffsetLabel;
	@UiField SpinnerValue subOffsetValue;

	private class ValueChangeTimer extends Timer {
		boolean updatePending = false;
    	
    	int TIMER = 600;
        String optionName;
        String value;
        AnswerHandler<Boolean> handler = new AnswerHandler<Boolean>() {
			
			@Override
			public void onAnswer(Boolean answer) {
				return;				
			}
		};

        public ValueChangeTimer(String optionName) {
            this.optionName = optionName;
        }

        public void updateValue(String value) {
        	// cancel old timer
        	if (this.updatePending) {
        		this.cancel();
        	}
        	
        	this.value = value;
        	this.updatePending = true;
        	this.schedule(TIMER);
        }
        
        @Override
        public void run() {
        	updatePending = false;
            ui.rpc.setPlayerOption(optionName, value, handler);
        }
    }
    private ValueChangeTimer zoomCommand = new ValueChangeTimer("zoom");
    private ValueChangeTimer subOffsetCommand = new ValueChangeTimer("sub_offset");
	
	public VideoOptionsPanel() {
		initWidget(uiBinder.createAndBindUi(this));
		
		zoomLabel.setText(ui.i18nConst.zoom());
		subOffsetLabel.setText(ui.i18nConst.subtitleOffset());
		
		ui.rpc.getAvailableVideoOptions(new AnswerHandler<HashMap<String,String>>() {
			
			@Override
			public void onAnswer(HashMap<String, String> answer) {
				hasZoom = Boolean.valueOf(answer.get("zoom"));
				zoomPanel.setVisible(hasZoom);
				zoomValue.addValueChangeHandler(new ValueChangeHandler<Integer>() {

					@Override
					public void onValueChange(ValueChangeEvent<Integer> event) {
						String v = Integer.toString(event.getValue());
						zoomCommand.updateValue(v);
					}
				});
				
				hasAspectRatio = Boolean.valueOf(answer.get("aspect_ratio"));
				aspectRatioPanel.setVisible(hasAspectRatio);
				
				hasSubOffset = Boolean.valueOf(answer.get("sub_offset"));
				if (hasSubOffset) {
					subOffsetValue.addValueChangeHandler(new ValueChangeHandler<Integer>() {

						@Override
						public void onValueChange(ValueChangeEvent<Integer> event) {
							String v = Integer.toString(event.getValue());
							subOffsetCommand.updateValue(v);
						}
					});
				}
			}
		});
		
		aspectRatioLabel.setText(ui.i18nConst.aspectRatio());
		aspectRatio.addChangeHandler(this);
		
		audioChannelLabel.setText(ui.i18nConst.audioChannel());
		audioChannel.addChangeHandler(this);
		subChannelLabel.setText(ui.i18nConst.subtitleChannel());
		subChannel.addChangeHandler(this);
		
	}

	@UiFactory
	public SpinnerValue makeSpinner() {
		return new SpinnerValue(true);
	}
	
	public void setAspectRatio(String value) {
        if (hasAspectRatio)
            selectListBoxItem(aspectRatio, value);
    }

    public void setZoom(long value) {
        if (hasZoom)
            zoomValue.setValue((int) value);
    }
    
    public void setSubOffset(long offset) {
        if (hasSubOffset)
            subOffsetValue.setValue((int) offset);
    }

    public void setAudioChannelEnabled(boolean enabled) {
    	audioChannelPanel.setVisible(enabled);
    }

    public void setAudioChannels(JSONArray channels, String value) {
        audioChannel.clear();
        for (int idx=0; idx<channels.size(); idx++) {
            JSONObject ch = channels.get(idx).isObject();
            audioChannel.addItem(ch.get("lang").isString().stringValue(),
                Integer.toString((int)ch.get("ix").isNumber().doubleValue()));
        }
        selectListBoxItem(audioChannel, value);
    }
    
    public void setSubChannelEnabled(boolean enabled) {
    	subChannelPanel.setVisible(enabled);
    	subOffsetPanel.setVisible(enabled & hasSubOffset);
    }

    public void setSubChannels(JSONArray channels, String value) {
        subChannel.clear();
        for (int idx=0; idx<channels.size(); idx++) {
            JSONObject ch = channels.get(idx).isObject();
            subChannel.addItem(ch.get("lang").isString().stringValue(),
                Integer.toString((int)ch.get("ix").isNumber().doubleValue()));
        }
        selectListBoxItem(subChannel, value);
    }
    
	public void onChange(ChangeEvent event) {
        ListBox source = (ListBox) event.getSource();
        String optionName = "";
        if (source == aspectRatio) {
            optionName = "aspect_ratio";
        } else if (source == audioChannel) {
            optionName = "audio_lang";
        } else if (source == subChannel) {
            optionName = "sub_lang";
        }
        ui.rpc.setPlayerOption(optionName,
                source.getValue(source.getSelectedIndex()), null);
    }
	
	private void selectListBoxItem(ListBox list, String value) {
        for (int idx=0; idx< list.getItemCount(); idx++) {
            if (list.getValue(idx).equals(value)) {
                list.setSelectedIndex(idx);
                break;
            }
        }
    }
}

//vim: ts=4 sw=4 expandtab