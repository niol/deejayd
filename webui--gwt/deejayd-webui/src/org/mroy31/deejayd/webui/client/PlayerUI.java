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
import org.mroy31.deejayd.common.rpc.GenericRpcCallback;
import org.mroy31.deejayd.common.widgets.DeejaydUtils;
import org.mroy31.deejayd.common.widgets.IsLayoutWidget;
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
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiFactory;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.Image;
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

    /*
     * RPC callbacks
     */
    class PlayerCallback extends GenericRpcCallback {
        public PlayerCallback(IsLayoutWidget ui) {super(ui);}
        public void onCorrectAnswer(JSONValue data) {
            ui.update();
        }
    }

    public PlayerUI(WebuiLayout webui) {
        this.resources = webui.resources;
        this.ui = webui;

        initWidget(uiBinder.createAndBindUi(this));
        // add player buttons handlers
        playToggleButton.addClickHandler(this);
        stopButton.addClickHandler(this);
        nextButton.addClickHandler(this);
        previousButton.addClickHandler(this);
        // add volume change handler
        volumeBar.addValueChangeHandler(new ValueChangeHandler<Double>() {
            public void onValueChange(ValueChangeEvent<Double> event) {
                int value = (int) Math.round(event.getValue());
                ui.rpc.setVolume(value, new PlayerCallback(ui));
            }
        });
        // add playing change handler
        playingTime.addClickHandler(this);
        seekBar.addValueChangeHandler(new ValueChangeHandler<Double>() {
            public void onValueChange(ValueChangeEvent<Double> event) {
                int value = (int) Math.round(event.getValue());
                ui.rpc.seek(value, new PlayerCallback(ui));
            }
        });

        // add status change handler
        ui.addStatusChangeHandler(this);
    }

    @UiFactory SliderBar makeSliderBar() {
        return new SliderBar(0, 100);
    }

    public void onClick(ClickEvent event) {
        Widget sender = (Widget) event.getSource();
        PlayerCallback callback = new PlayerCallback(ui);
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
        }
    }

    public void onStatusChange(StatusChangeEvent event) {
        HashMap<String, String> status = event.getStatus();
        // update play toggle button
        if (status.get("state").equals("play")) {
            playToggleButton.setStyleName(resources.webuiCss().pauseButton()+
                    " "+resources.webuiCss().playerButton());
        } else {
            playToggleButton.setStyleName(resources.webuiCss().playButton()+
                    " "+resources.webuiCss().playerButton());
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
            if (!status.get("current").equals(this.current)) {
                ui.rpc.getCurrent(new CurrentCallback(ui));
                this.current = status.get("current");
            }
            playingPanel.setVisible(true);
            if (!this.currentTime.equals(status.get("time"))) {
                String[] times = status.get("time").split(":");
                seekBar.setMaxValue(Integer.parseInt(times[1]));
                seekBar.setCurrentValue(Integer.parseInt(times[0]), false);
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
            int mediaId = (int) Math.round(media.get("media_id").isNumber().doubleValue());
            ui.rpc.getCover(mediaId, new CoverCallback(ui));
        } else if (type.equals("video")) {
            int length = (int) media.get("length").isNumber().doubleValue();
            title = media.get("title").isString().stringValue() + " (" +
                DeejaydUtils.formatTime(length) + ")";
        } else if (type.equals("webradio")) {
            // TODO
        }
        playingTitle.setHTML(title);
        playingDesc.setHTML(desc);
    }

    protected void clearPlayingArea() {
        playingPanel.setVisible(false);
        coverPanel.setVisible(false);
    }

    protected void updateCover(JSONString cover) {
        if (cover != null) {
            String url = GWT.getHostPageBaseURL()+"../"+cover.stringValue();
            coverImage.setUrl(url);
            coverPanel.setVisible(true);
        }
    }
}

//vim: ts=4 sw=4 expandtab