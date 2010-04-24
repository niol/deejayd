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
import org.mroy31.deejayd.common.rpc.DefaultRpcCallback;
import org.mroy31.deejayd.common.widgets.DeejaydUtils;
import org.mroy31.deejayd.common.widgets.PlayerWidget;
import org.mroy31.deejayd.webui.resources.WebuiResources;
import org.mroy31.deejayd.webui.widgets.SliderBar;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiFactory;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.PopupPanel;
import com.google.gwt.user.client.ui.Widget;

public class PlayerUI extends PlayerWidget
        implements ClickHandler, StatusChangeHandler {

    private static PlayerUIUiBinder uiBinder = GWT
            .create(PlayerUIUiBinder.class);
    interface PlayerUIUiBinder extends UiBinder<Widget, PlayerUI> {}

    @UiField(provided = true) final WebuiResources resources;
    @UiField SliderBar volumeBar;
    @UiField Button playToggleButton;
    @UiField Button stopButton;
    @UiField Button nextButton;
    @UiField Button previousButton;

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

    private class SeekTimer extends Timer {
        private int value;
        public SeekTimer(int seekTime) {
            value = seekTime;
        }

        public void run() {
            ui.rpc.seek(value, new DefaultRpcCallback(ui));
        }
    }
    private SeekTimer seekTimer = null;

    private class VolumeTimer extends Timer {
        private int value;
        public VolumeTimer(int volume) {
            value = volume;
        }

        public void run() {
            ui.rpc.setVolume(value, new DefaultRpcCallback(ui));
        }
    }
    private VolumeTimer volumeTimer = null;

    public PlayerUI(WebuiLayout webui) {
        this.ui = webui;
        this.resources = webui.resources;

        initWidget(uiBinder.createAndBindUi(this));
        // add player buttons handlers
        playToggleButton.addClickHandler(this);
        stopButton.addClickHandler(this);
        nextButton.addClickHandler(this);
        previousButton.addClickHandler(this);
        // add volume change handler
        volumeBar.setStepSize(5);
        volumeBar.addValueChangeHandler(new ValueChangeHandler<Double>() {
            public void onValueChange(ValueChangeEvent<Double> event) {
                int value = (int) Math.round(event.getValue());
                if (volumeTimer != null) {
                    volumeTimer.cancel();
                    volumeTimer = null;
                }
                volumeTimer = new VolumeTimer(value);
                volumeTimer.schedule(200);
            }
        });
        seekPanel.setSpacing(2);
        seekPanel.setCellVerticalAlignment(playingTime,
                HorizontalPanel.ALIGN_MIDDLE);
        // add playing change handler
        playingTime.addClickHandler(this);
        seekBar.setStepSize(10);
        seekBar.addValueChangeHandler(new ValueChangeHandler<Double>() {
            public void onValueChange(ValueChangeEvent<Double> event) {
                int value = (int) Math.round(event.getValue());
                if (seekTimer != null) {
                    seekTimer.cancel();
                    seekTimer = null;
                }
                playingTime.setText(DeejaydUtils.formatTime(value)+"-->");
                seekTimer = new SeekTimer(value);
                seekTimer.schedule(200);
            }
        });
        // init video options
        optionButton.addClickHandler(this);
        videoOptions = new VideoOptions(ui);

        // add status change handler
        ui.addStatusChangeHandler(this);
    }

    @UiFactory SliderBar makeSliderBar() {
        return new SliderBar(0, 100, resources);
    }

    public void onClick(ClickEvent event) {
        Widget sender = (Widget) event.getSource();
        DefaultRpcCallback callback = new DefaultRpcCallback(ui);
        if (sender == playToggleButton) {
            ui.rpc.playToggle(callback);
        } else if (sender == stopButton) {
            ui.rpc.stop(callback);
        } else if (sender == nextButton) {
            ui.rpc.next(callback);
        } else if (sender == previousButton) {
            ui.rpc.previous(callback);
        } else if (sender == playingTime) {
            seekBar.setVisible(!seekBar.isVisible());
            if (seekBar.isVisible()) {
                seekBar.drawKnob();
            }
        } else if (sender == optionButton) {
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
                ui.rpc.getCurrent(new CurrentCallback(ui));
                this.current = status.get("current");
                seekBar.setMaxValue(Integer.parseInt(times[1]));
                this.currentTime = "";
            } else {
                String[] currentState = this.current.split(":");
                if (currentState[2].equals("webradio")
                        || currentState[2].equals("video")) {
                    ui.rpc.getCurrent(new CurrentCallback(ui));
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

    protected void formatCurrentTitle(JSONObject media) {
        String title = "";
        String desc = "";
        String type = media.get("type").isString().stringValue();

        optionButton.setVisible(type.equals("video"));
        if (type.equals("song")) {
            String length = media.get("length").isString().stringValue();
            title = media.get("title").isString().stringValue() + " (" +
                DeejaydUtils.formatTime(Integer.parseInt(length)) + ")";
            JSONString artist = media.get("artist").isString();
            JSONString album = media.get("album").isString();
            if (artist != null) {
                desc += artist.stringValue()+" - ";
            }
            if (album != null) {
                desc += "<b>"+album.stringValue()+"<b>";
            }

            // get cover
            int mediaId = (int) Math.round(
                    media.get("media_id").isNumber().doubleValue());
            ui.rpc.getCover(mediaId, new CoverCallback(ui));
        } else if (type.equals("video")) {
            String length = media.get("length").isString().stringValue();
            title = media.get("title").isString().stringValue() + " (" +
                DeejaydUtils.formatTime(Integer.parseInt(length)) + ")";
            setVideoOptions(media);
        } else if (type.equals("webradio")) {
            title = media.get("title").isString().stringValue();
            if (media.get("song-title") != null) {
                title +=" -- "+media.get("song-title").isString().stringValue();
            }
            if (media.get("uri") != null) {
                desc = media.get("uri").isString().stringValue();
            }
        }
        playingTitle.setHTML(title);
        playingDesc.setHTML(desc);
    }

    protected void clearPlayingArea() {
        playingPanel.setVisible(false);
        videoOptions.hide();
        coverPanel.setVisible(false);
    }

    protected void updateCover(JSONString cover) {
        if (cover != null) {
            String url = GWT.getHostPageBaseURL()+"../"+cover.stringValue();
            coverImage.setUrl(url);
            coverPanel.setVisible(true);
        }
    }

    protected void setVideoOptions(JSONObject media) {
        long avOffset = (long) media.get("av_offset").isNumber().doubleValue();
        videoOptions.setAVOffset(avOffset);
        long zoom = (long) media.get("zoom").isNumber().doubleValue();
        videoOptions.setZoom(zoom);
        String aspectRatio = media.get("aspect_ratio").isString().stringValue();
        videoOptions.setAspectRatio(aspectRatio);

        boolean hasAudioChannel = media.get("audio") != null;
        videoOptions.setAudioChannelEnabled(hasAudioChannel);
        if (hasAudioChannel) {
            String value = Integer.toString(
                    (int)media.get("audio_idx").isNumber().doubleValue());
            videoOptions.setAudioChannels(media.get("audio").isArray(), value);
        }

        boolean hasSubChannel = media.get("subtitle") != null;
        videoOptions.setSubChannelEnabled(hasSubChannel);
        if (hasSubChannel) {
            String value = Integer.toString(
                    (int)media.get("subtitle_idx").isNumber().doubleValue());
            videoOptions.setSubChannels(media.get("subtitle").isArray(), value);
            videoOptions.setSubOffset(
                    (long)media.get("sub_offset").isNumber().doubleValue());
        }
    }
}

//vim: ts=4 sw=4 expandtab