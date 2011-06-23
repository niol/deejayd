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
 *
 * This Widget is mainly based on SpinnerValue from gwt-incubator project
 */

package org.mroy31.deejayd.webui.client;

import java.util.HashMap;

import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.webui.widgets.ValueSpinner;

import com.google.gwt.event.dom.client.ChangeEvent;
import com.google.gwt.event.dom.client.ChangeHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.ui.FlexTable;
import com.google.gwt.user.client.ui.ListBox;
import com.google.gwt.user.client.ui.PopupPanel;
import com.google.gwt.user.client.ui.Widget;

public class VideoOptions extends PopupPanel
        implements ValueChangeHandler<Long>, ChangeHandler{
    private WebuiLayout ui;
    private boolean has_avoffset = false;
    private boolean has_suboffset = false;
    private boolean has_zoom = false;
    private boolean has_aspectratio = false;

    private FlexTable panel = new FlexTable();
    private ValueSpinner avOffset;
    private ValueSpinner zoom;
    private ListBox aspectRatio = new ListBox();

    private int audioChannelRow = -1;
    private ListBox audioChannel = new ListBox();
    private int subChannelRow = -1;
    private ListBox subChannel = new ListBox();
    private ValueSpinner subOffset = null;

    private class ValueChangeCommand extends Timer {
        private Widget source;
        private String value;

        public ValueChangeCommand(Widget source, String value) {
            this.source = source;
            this.value = value;
        }

        public Widget getSource() {
            return source;
        }

        @Override
        public void run() {
            String optName = "";
            if (source == avOffset) {
               optName = "av_offset";
            } else if (source == zoom) {
                optName = "zoom";
            } else if (source == subOffset) {
                optName = "sub_offset";
            }
            ui.rpc.setPlayerOption(optName, value, null);

        }
    }
    private ValueChangeCommand command;

    public VideoOptions(WebuiLayout webui) {
        this.ui = webui;
        setWidget(panel);

        audioChannel.addChangeHandler(this);
        subChannel.addChangeHandler(this);

        final VideoOptions instance = this;
        ui.rpc.getAvailableVideoOptions(new AnswerHandler<HashMap<String,String>>() {

            public void onAnswer(HashMap<String, String> answer) {
                int idx = 0;

                has_zoom = Boolean.valueOf(answer.get("zoom"));
                if (has_zoom) { // zoom
                    zoom = new ValueSpinner(ui.resources, 0, -85, 400, 5, 5, true);
                    panel.setText(idx, 0, ui.i18nConstants.zoom());
                    panel.setWidget(idx, 1, zoom);
                    zoom.addValueChangeHandler(instance);
                    idx ++;
                }

                has_aspectratio = Boolean.valueOf(answer.get("aspect_ration"));
                if (has_aspectratio) { // aspect ratio
                    aspectRatio.addItem("Auto", "auto");
                    aspectRatio.addItem("1:1");
                    aspectRatio.addItem("16:9");
                    aspectRatio.addItem("4:3");
                    aspectRatio.addItem("DVB (2.11:1)", "2.11:1");
                    panel.setText(idx, 0, ui.i18nConstants.aspectRatio());
                    panel.setWidget(idx, 1, aspectRatio);
                    aspectRatio.addChangeHandler(instance);
                    idx ++;
                }

                has_avoffset = Boolean.valueOf(answer.get("av_offset"));
                if (has_avoffset) { // Audio/Video Offset
                    avOffset = new ValueSpinner(ui.resources, 0, 0, 0, 100, 100, false);
                    panel.setText(idx, 0, ui.i18nConstants.avOffset());
                    panel.setWidget(idx, 1, avOffset);
                    avOffset.addValueChangeHandler(instance);
                    idx ++;
                }

                has_suboffset = Boolean.valueOf(answer.get("sub_offset"));
                if (has_suboffset) { // subtitles Offset
                    subOffset = new ValueSpinner(ui.resources, 0, 0, 0, 100, 100, false);
                    subOffset.addValueChangeHandler(instance);
                }
            }
        });
    }

    public void setAVOffset(long delta) {
        if (has_avoffset)
            avOffset.setValue(delta);
    }

    public void setAspectRatio(String value) {
        if (has_aspectratio)
            selectListBoxItem(aspectRatio, value);
    }

    public void setZoom(long zoomValue) {
        if (has_zoom)
            zoom.setValue(zoomValue);
    }

    public void setAudioChannelEnabled(boolean enabled) {
        if (enabled && audioChannelRow == -1) {
            audioChannelRow = panel.getRowCount();
            panel.setText(audioChannelRow, 0, ui.i18nConstants.audioChannels());
            panel.setWidget(audioChannelRow, 1, audioChannel);
        } else if (!enabled && audioChannelRow != -1) {
            panel.removeRow(audioChannelRow);
            audioChannelRow = -1;
        }
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
        if (enabled && subChannelRow == -1) {
            subChannelRow = panel.getRowCount();
            panel.setText(subChannelRow, 0, ui.i18nConstants.subChannels());
            panel.setWidget(subChannelRow, 1, subChannel);

            if (subOffset != null) {
                panel.setText(subChannelRow+1, 0, ui.i18nConstants.subOffset());
                panel.setWidget(subChannelRow+1, 1, subOffset);
            }
        } else if (!enabled && subChannelRow != -1) {
            panel.removeRow(subChannelRow);
            if (subOffset != null) {
                panel.removeRow(subChannelRow);
            }
            subChannelRow = -1;
        }
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

    public void setSubOffset(long offset) {
        if (has_suboffset)
            subOffset.setValue(offset);
    }

    public void onValueChange(ValueChangeEvent<Long> event) {
        Widget source = (Widget) event.getSource();
        if (command != null && command.getSource() == source)
            command.cancel();
        command = new ValueChangeCommand(source,
                Long.toString(event.getValue()));
        command.schedule(300);
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