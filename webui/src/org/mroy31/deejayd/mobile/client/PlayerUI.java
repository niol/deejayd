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
import org.mroy31.deejayd.mobile.widgets.VolumeSlider;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.LoadEvent;
import com.google.gwt.event.dom.client.LoadHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Widget;

public class PlayerUI extends PlayerWidget {
    private final MobileLayout ui = MobileLayout.getInstance();

    private static PlayerUIUiBinder uiBinder = GWT
            .create(PlayerUIUiBinder.class);
    interface PlayerUIUiBinder extends UiBinder<Widget, PlayerUI> {}

    public interface MediaChangeHandler {
        public void onMediaChange(String title);
    }
    private MediaChangeHandler changeHandler;

    @UiField HorizontalPanel seekBarPanel;
    @UiField TimeSeekBar seekBar;
    @UiField VolumeSlider volSlider;
    @UiField Image coverImg;
    @UiField Button playToggleButton;
    @UiField(provided = true) final MobileResources resources = ui.resources;

    public PlayerUI(MediaChangeHandler handler) {
        super(MobileLayout.getInstance());

        this.changeHandler = handler;
        initWidget(uiBinder.createAndBindUi(this));

        coverImg.addLoadHandler(new LoadHandler() {
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
            public void onValueChange(ValueChangeEvent<Integer> event) {
                if (volumeTimer != null) {
                    volumeTimer.cancel();
                }
                volumeTimer = new VolumeTimer(event.getValue());
                volumeTimer.schedule(400);
            }
        });

        // Time SeekBar
        seekBar.addValueChangeHandler(new ValueChangeHandler<Integer>() {
            public void onValueChange(ValueChangeEvent<Integer> event) {
                if (seekTimer != null) {
                    seekTimer.cancel();
                }
                seekTimer = new SeekTimer(event.getValue());
                seekTimer.schedule(250);
            }
        });
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
        ui.rpc.getCurrent(new AnswerHandler<Media>() {

            public void onAnswer(Media current) {
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
                    title += " ("+DeejaydUtils.formatTime(current.getIntAttr("length"))+")";
                } else if (current.isWebradio()) {
                    if (current.hasAttr("song-title"))
                        title += " -- " + current.getStrAttr("song-title");
                    if (current.hasAttr("uri"))
                        desc = current.getStrAttr("uri");
                }

                changeHandler.onMediaChange("<b>"+title+"</b><br/><i>"+desc+"</i>");
            }
        });
    }

    public void resetCover() {
        coverImg.setResource(ui.resources.missingCover());
    }

}

//vim: ts=4 sw=4 expandtab