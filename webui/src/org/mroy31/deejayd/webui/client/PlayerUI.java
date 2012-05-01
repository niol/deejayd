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

package org.mroy31.deejayd.webui.client;

import java.util.HashMap;

import org.mroy31.deejayd.common.events.StatusChangeEvent;
import org.mroy31.deejayd.common.events.StatusChangeHandler;
import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.common.rpc.types.Media;
import org.mroy31.deejayd.common.widgets.DeejaydUtils;
import org.mroy31.deejayd.common.widgets.PlayerWidget;
import org.mroy31.deejayd.webui.resources.WebuiResources;
import org.mroy31.deejayd.webui.widgets.SliderBar;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiFactory;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.uibinder.client.UiHandler;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.PopupPanel;
import com.google.gwt.user.client.ui.Widget;

public class PlayerUI extends PlayerWidget implements StatusChangeHandler {

    private static PlayerUIUiBinder uiBinder = GWT
            .create(PlayerUIUiBinder.class);
    interface PlayerUIUiBinder extends UiBinder<Widget, PlayerUI> {}

    @UiField(provided = true) final WebuiResources resources;
    @UiField SliderBar volumeBar;
    @UiField Button playToggleButton;

    @UiField FlowPanel playingPanel;
    @UiField HorizontalPanel seekPanel;
    @UiField SliderBar seekBar;
    @UiField HTML playingTitle;
    @UiField HTML playingDesc;
    @UiField Button playingTime;
    @UiField Button optionButton;
    @UiField FlowPanel coverPanel;
    @UiField Image coverImage;

    private WebuiLayout ui;
    private String current = "";
    private String currentTime = "";
    private VideoOptions videoOptions;

    public PlayerUI(WebuiLayout webui) {
        super(webui);

        this.ui = webui;
        this.resources = webui.resources;

        initWidget(uiBinder.createAndBindUi(this));
        // add volume change handler
        volumeBar.setStepSize(5);
        volumeBar.addValueChangeHandler(new ValueChangeHandler<Double>() {
            public void onValueChange(ValueChangeEvent<Double> event) {
                int value = (int) Math.round(event.getValue());
                volumeTimer.updateValue(value);
            }
        });
        // add playing change handler
        seekBar.setStepSize(10);
        seekBar.addValueChangeHandler(new ValueChangeHandler<Double>() {
            public void onValueChange(ValueChangeEvent<Double> event) {
                int value = (int) Math.round(event.getValue());
                playingTime.setText(DeejaydUtils.formatTime(value)+"-->");
                seekTimer.updateValue(value);
            }
        });
        // init video options
        videoOptions = new VideoOptions(ui);

        // add status change handler
        ui.addStatusChangeHandler(this);
    }

    @UiFactory SliderBar makeSliderBar() {
        return new SliderBar(0, 100, resources);
    }

    @UiHandler("playingTime")
    public void playingButtonHandler(ClickEvent event) {
        seekBar.setVisible(!seekBar.isVisible());
        if (seekBar.isVisible()) {
            seekBar.drawKnob();
        }
    }

    @UiHandler("optionButton")
    public void optionButtonHandler(ClickEvent event) {
        if (videoOptions.isShowing()) {
            videoOptions.hide();
        } else {
            videoOptions.setPopupPositionAndShow(
                    new PopupPanel.PositionCallback() {
                        public void setPosition(int offsetWidth,
                                int offsetHeight) {
                            int left = optionButton.getAbsoluteLeft() +
                                optionButton.getOffsetWidth();
                            int top = optionButton.getAbsoluteTop();
                            videoOptions.setPopupPosition(left, top);
                  }
            });
        }
    }

    public void onStatusChange(StatusChangeEvent event) {
        HashMap<String, String> status = event.getStatus();
        // update play toggle button
        if (status.get("state").equals("play")) {
            playToggleButton.setStyleName(resources.webuiCss().pauseButton()+
                    " "+resources.webuiCss().iconOnlyButton());
        } else {
            playToggleButton.setStyleName(resources.webuiCss().playButton()+
                    " "+resources.webuiCss().iconOnlyButton());
        }

        // update volume bar
        double volume = Double.parseDouble(status.get("volume"));
        volumeBar.setCurrentValue(volume, false);

        // update current media
        if (status.get("state").equals("stop")) {
            clearPlayingArea();
            this.current = "";
            this.currentTime = "";
        } else {
            String[] times = status.get("time").split(":");
            if (!status.get("current").equals(this.current)) {
                videoOptions.hide();
                updateCurrent();
                this.current = status.get("current");
                seekBar.setMaxValue(Integer.parseInt(times[1]));
                this.currentTime = "";
            } else {
                String[] currentState = this.current.split(":");
                if (currentState[2].equals("webradio")
                        || currentState[2].equals("video")) {
                    updateCurrent();
                }
            }
            playingPanel.setVisible(true);
            if (!this.currentTime.equals(status.get("time"))) {
                double time = Double.parseDouble(times[0]);
                seekBar.setCurrentValue(time, false);
                playingTime.setText(DeejaydUtils.formatTime((int) time)+"-->");
                this.currentTime = status.get("time");
            }
        }
    }

    private void updateCurrent() {
        ui.rpc.getCurrent(new AnswerHandler<Media>() {

            public void onAnswer(Media answer) {
                playingTitle.setHTML(answer.formatTitle());
                playingDesc.setHTML(answer.formatDesc());
                optionButton.setVisible(answer.isVideo());

                if (answer.isSong()) {
                    // get cover
                    ui.rpc.getCover(answer.getMediaId(),
                            new AnswerHandler<HashMap<String,String>>() {
                        public void onAnswer(HashMap<String, String> answer) {
                            if (!answer.containsKey("cover")) {
                                coverPanel.setVisible(false);
                                return;
                            }
                            String cover = answer.get("cover");
                            String url = GWT.getHostPageBaseURL()+"../"+cover;
                            coverImage.setUrl(url);
                            coverPanel.setVisible(true);
                        }
                    });
                } else if (answer.isVideo()) {
                    setVideoOptions(answer);
                }
            }
        });
    }

    protected void clearPlayingArea() {
        playingPanel.setVisible(false);
        videoOptions.hide();
        coverPanel.setVisible(false);
    }

    protected void setVideoOptions(Media media) {
        videoOptions.setAVOffset((long) media.getIntAttr("av_offset"));
        videoOptions.setZoom((long) media.getIntAttr("zoom"));
        videoOptions.setAspectRatio(media.getStrAttr("aspect_ratio"));

        videoOptions.setAudioChannelEnabled(media.hasAttr("audio"));
        if (media.hasAttr("audio")) {
            String value = media.getStrAttr("audio_idx");
            videoOptions.setAudioChannels(media.getArrayAttr("audio"), value);
        }

        videoOptions.setSubChannelEnabled(media.hasAttr("subtitle"));
        if (media.hasAttr("subtitle")) {
            String value = media.getStrAttr("subtitle_idx");
            videoOptions.setSubChannels(media.getArrayAttr("subtitle"), value);
            videoOptions.setSubOffset((long) media.getIntAttr("sub_offset"));
        }
    }
}

//vim: ts=4 sw=4 expandtab