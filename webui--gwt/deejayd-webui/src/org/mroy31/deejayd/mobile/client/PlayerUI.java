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

import org.mroy31.deejayd.common.rpc.DefaultRpcCallback;
import org.mroy31.deejayd.common.widgets.DeejaydUtils;
import org.mroy31.deejayd.common.widgets.PlayerWidget;
import org.mroy31.deejayd.mobile.resources.MobileResources;
import org.mroy31.deejayd.mobile.widgets.TimeSeekBar;
import org.mroy31.deejayd.mobile.widgets.VolumeSlider;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.dom.client.LoadEvent;
import com.google.gwt.event.dom.client.LoadHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Widget;

public class PlayerUI extends PlayerWidget implements ClickHandler {
    private final MobileLayout ui = MobileLayout.getInstance();

    private static PlayerUIUiBinder uiBinder = GWT
            .create(PlayerUIUiBinder.class);

    interface PlayerUIUiBinder extends UiBinder<Widget, PlayerUI> {}
    public interface MediaChangeHandler {
        public void onMediaChange(String title);
    }
    private MediaChangeHandler changeHandler;

    private class VolumeTimer extends Timer {
        private int value;
        public VolumeTimer(int value) {
            this.value = value;
        }

        @Override
        public void run() {
            ui.rpc.setVolume(value, new DefaultRpcCallback(ui));
        }
    };
    private VolumeTimer volTimer = null;

    private class SeekTimer extends Timer {
        private int value;
        public SeekTimer(int seekTime) {
            value = seekTime;
        }

        @Override
        public void run() {
            ui.rpc.seek(value, new DefaultRpcCallback(ui));
        }
    }
    private SeekTimer seekTimer = null;

    @UiField HorizontalPanel seekBarPanel;
    @UiField TimeSeekBar seekBar;
    @UiField VolumeSlider volSlider;
    @UiField Image coverImg;
    @UiField Button previousButton;
    @UiField Button playToggleButton;
    @UiField Button stopButton;
    @UiField Button nextButton;
    @UiField(provided = true) final MobileResources resources = ui.resources;

    public PlayerUI(MediaChangeHandler handler) {
        this.changeHandler = handler;
        initWidget(uiBinder.createAndBindUi(this));

        for (Button btn : new Button[]{previousButton, playToggleButton,
                stopButton, nextButton}) {
            btn.addClickHandler(this);
        }
        coverImg.addLoadHandler(new LoadHandler() {
            @Override
            public void onLoad(LoadEvent event) {
                int size = Math.min(Window.getClientWidth(),
                        Window.getClientHeight()-140);
                coverImg.setHeight(Integer.toString(size));
                coverImg.setWidth(Integer.toString(size));
            }
        });
        coverImg.setResource(ui.resources.missingCover());

        // Volume slider
        volSlider.addValueChangeHandler(new ValueChangeHandler<Integer>() {
            @Override
            public void onValueChange(ValueChangeEvent<Integer> event) {
                if (volTimer != null) {
                    volTimer.cancel();
                }
                volTimer = new VolumeTimer(event.getValue());
                volTimer.schedule(400);
            }
        });

        // Time SeekBar
        seekBarPanel.setCellHorizontalAlignment(seekBar,
                HorizontalPanel.ALIGN_CENTER);
        seekBar.addValueChangeHandler(new ValueChangeHandler<Integer>() {
            @Override
            public void onValueChange(ValueChangeEvent<Integer> event) {
                if (seekTimer != null) {
                    seekTimer.cancel();
                }
                seekTimer = new SeekTimer(event.getValue());
                seekTimer.schedule(250);
            }
        });
    }

    @Override
    protected void formatCurrentTitle(JSONObject media) {
        String title = "";
        String desc = "";
        String type = media.get("type").isString().stringValue();

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
                desc += album.stringValue();
            }

            // get cover
            int mediaId = (int) Math.round(
                    media.get("media_id").isNumber().doubleValue());
            ui.rpc.getCover(mediaId, new CoverCallback(ui));
        } else if (type.equals("video")) {
            String length = media.get("length").isString().stringValue();
            title = media.get("title").isString().stringValue() + " (" +
                DeejaydUtils.formatTime(Integer.parseInt(length)) + ")";
        } else if (type.equals("webradio")) {
            title = media.get("title").isString().stringValue();
            if (media.get("song-title") != null) {
                title +=" -- "+media.get("song-title")
                        .isString().stringValue();
            }
            if (media.get("uri") != null) {
                desc = media.get("uri").isString().stringValue();
            }
        }

        changeHandler.onMediaChange("<b>"+title+"</b><br/><i>"+desc+"</i>");
    }

    public void updateState(String state) {
        if (state.equals("play")) {
            playToggleButton.addStyleName(ui.resources.mobileCss().pause());
            playToggleButton.removeStyleName(
                    ui.resources.mobileCss().play());
        } else {
            playToggleButton.addStyleName(ui.resources.mobileCss().play());
            playToggleButton.removeStyleName(
                    ui.resources.mobileCss().pause());
        }
        seekBar.setVisible(!state.equals("stop"));
    }

    public void updateVolume(int vol) {
        volSlider.setCurrentValue(vol, false);
    }

    public void updateCurrent() {
        ui.rpc.getCurrent(new CurrentCallback(ui));
    }

    @Override
    protected void updateCover(JSONString cover) {
        if (cover != null) {
            String url = GWT.getHostPageBaseURL()+"../"+cover.stringValue();
            coverImg.setUrl(url);
        }
    }

    public void resetCover() {
        coverImg.setResource(ui.resources.missingCover());
    }

    @Override
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
        }
    }

}

//vim: ts=4 sw=4 expandtab