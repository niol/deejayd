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
import org.mroy31.deejayd.common.rpc.types.Media;
import org.mroy31.deejayd.common.widgets.DeejaydUtils;
import org.mroy31.deejayd.common.widgets.PlayerWidget;
import org.mroy31.deejayd.mobile.resources.MobileResources;
import org.mroy31.deejayd.mobile.widgets.TimeSeekBar;
import org.mroy31.deejayd.mobile.widgets.VolumeControl;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.LoadEvent;
import com.google.gwt.event.dom.client.LoadHandler;
import com.google.gwt.event.logical.shared.ResizeEvent;
import com.google.gwt.event.logical.shared.ResizeHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.uibinder.client.UiHandler;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Widget;

public class PlayerUI extends PlayerWidget {
    private final MobileLayout ui = MobileLayout.getInstance();
    private PlayerPanel playerPanel;

    private static PlayerUIUiBinder uiBinder = GWT
            .create(PlayerUIUiBinder.class);
    interface PlayerUIUiBinder extends UiBinder<Widget, PlayerUI> {}

    public interface MediaChangeHandler {
        public void onMediaChange(String title);
    }
    private MediaChangeHandler changeHandler;
    private Media currentMedia = null;
    private String state = "stop";
    
    private VideoOptionsPanel videoOptsPanel = new VideoOptionsPanel();
    private GoToPanel goToPanel = new GoToPanel();

    @UiField FlowPanel optionPanel;
    @UiField TimeSeekBar seekBar;
    @UiField VolumeControl volSlider;
    @UiField Image coverImg;
    @UiField Button videoOptsButton;
    @UiField Button seekButton;
    @UiField Button playToggleButton;
    @UiField(provided = true) final MobileResources resources = ui.resources;

    public PlayerUI(MediaChangeHandler handler, PlayerPanel playerPanel) {
        super(MobileLayout.getInstance());
        this.playerPanel = playerPanel;

        this.changeHandler = handler;
        initWidget(uiBinder.createAndBindUi(this));

        coverImg.addLoadHandler(new LoadHandler() {
            public void onLoad(LoadEvent event) {
                resizeCoverImage();
            }
        });
        coverImg.setResource(ui.resources.missingCover());
        // resize cover img when window is resized
        Window.addResizeHandler(new ResizeHandler() {
			
			@Override
			public void onResize(ResizeEvent event) {
				resizeCoverImage();
			}
		});

        // Volume slider
        volSlider.addValueChangeHandler(new ValueChangeHandler<Integer>() {
            public void onValueChange(ValueChangeEvent<Integer> event) {
                volumeTimer.updateValue(event.getValue());
            }
        });

        // Time SeekBar
        seekButton.setText(ui.i18nConst.goTo());
        seekBar.addValueChangeHandler(new ValueChangeHandler<Integer>() {
            public void onValueChange(ValueChangeEvent<Integer> event) {
                seekTimer.updateValue(event.getValue());
            }
        });
        
        // video options
        videoOptsButton.setText(ui.i18nConst.videoOption());
    }

    public void updateState(String state) {
    	this.state = state;
        if (state.equals("play")) {
            playToggleButton.addStyleName(ui.resources.mobileCss().pause());
            playToggleButton.removeStyleName(
                    ui.resources.mobileCss().play());
        } else {
            playToggleButton.addStyleName(ui.resources.mobileCss().play());
            playToggleButton.removeStyleName(
                    ui.resources.mobileCss().pause());
        }    
        updateOptionPanelDisplay();
    }
    
    public void updateVolume(int vol) {
        volSlider.setValue(vol, false);
    }

    public void updateCurrent() {
        ui.rpc.getCurrent(new AnswerHandler<Media>() {

            public void onAnswer(Media current) {
            	currentMedia = current;
            	
                String title = current.getStrAttr("title");
                String desc = "";

                if (current.isSong()) {
                    title += " ("+DeejaydUtils.formatTime(current.getIntAttr("length"))+")";
                    if (current.hasAttr("artist"))
                        desc += current.getStrAttr("artist");
                    if (current.hasAttr("album"))
                        desc += " - " + current.getStrAttr("album");

                    // get cover
                    ui.rpc.getCover(current.getMediaId(), new AnswerHandler<HashMap<String,String>>() {
                        public void onAnswer(HashMap<String, String> answer) {
                            if (!answer.containsKey("cover"))
                                return;
                            String cover = answer.get("cover");
                            String url = GWT.getHostPageBaseURL()+"../"+cover;
                            coverImg.setUrl(url);
                        }
                    });
                } else if (current.isVideo()) {
                    resetCover();
                    title += " ("+DeejaydUtils.formatTime(current.getIntAttr("length"))+")";
                    setVideoOptions(current);
                } else if (current.isWebradio()) {
                    resetCover();
                    if (current.hasAttr("song-title"))
                        title += " -- " + current.getStrAttr("song-title");
                    if (current.hasAttr("uri"))
                        desc = current.getStrAttr("uri");
                }
                videoOptsButton.setVisible(current.isVideo());
                updateOptionPanelDisplay();

                changeHandler.onMediaChange("<b>"+title+"</b><br/><i>"+desc+"</i>");
            }
        });
    }

    public void resetCover() {
        coverImg.setResource(ui.resources.missingCover());
    }

    @UiHandler("seekButton")
    void seekButtonHandler(ClickEvent e) {
    	playerPanel.setContextWidget(ui.i18nConst.goTo(), goToPanel);
    	playerPanel.setContextVisible(true);
    }
    
    @UiHandler("videoOptsButton")
    void videoOptsButtonHandler(ClickEvent e) {
    	playerPanel.setContextWidget(ui.i18nConst.videoOption(), videoOptsPanel);
    	playerPanel.setContextVisible(true);
    }
    
    protected void setVideoOptions(Media media) {
        videoOptsPanel.setZoom((long) media.getIntAttr("zoom"));
        videoOptsPanel.setAspectRatio(media.getStrAttr("aspect_ratio"));

        videoOptsPanel.setAudioChannelEnabled(media.hasAttr("audio"));
        if (media.hasAttr("audio")) {
            String value = media.getStrAttr("audio_idx");
            videoOptsPanel.setAudioChannels(media.getArrayAttr("audio"), value);
        }

        videoOptsPanel.setSubChannelEnabled(media.hasAttr("subtitle"));
        if (media.hasAttr("subtitle")) {
            String value = media.getStrAttr("subtitle_idx");
            videoOptsPanel.setSubChannels(media.getArrayAttr("subtitle"), value);
            videoOptsPanel.setSubOffset((long) media.getIntAttr("sub_offset"));
        }
    }
    
    private void resizeCoverImage() {
    	int size = Math.min(Window.getClientWidth(),
                Window.getClientHeight()-140);
        coverImg.setHeight(Integer.toString(size));
        coverImg.setWidth(Integer.toString(size));
    }
    
    private void updateOptionPanelDisplay() {
    	optionPanel.setVisible((!state.equals("stop")) 
        		&& (currentMedia != null) 
        		&& (!currentMedia.isWebradio()));
    }

}

//vim: ts=4 sw=4 expandtab