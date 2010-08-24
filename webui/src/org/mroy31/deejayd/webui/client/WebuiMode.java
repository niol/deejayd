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

import org.mroy31.deejayd.common.rpc.DefaultRpcCallback;
import org.mroy31.deejayd.webui.medialist.MediaList;

import com.google.gwt.event.dom.client.ChangeEvent;
import com.google.gwt.event.dom.client.ChangeHandler;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.ListBox;
import com.google.gwt.user.client.ui.Widget;

public abstract class WebuiMode extends Composite
        implements WebuiModeInterface {
    protected String sourceName;
    protected WebuiLayout ui;
    protected int currentPlayingPos = -1;
    protected int mediaId = -1;
    protected int selectionLength = 0;

    public boolean hasPlayorder;
    protected ListBox podrList;
    public boolean hasRepeat;
    protected CheckBox repeatCk;

    public WebuiMode(String source, WebuiLayout webui,
            boolean hasPlayorder, boolean hasRepeat) {
        this.ui = webui;
        this.sourceName = source;
        this.hasPlayorder = hasPlayorder;
        this.hasRepeat = hasRepeat;
    }

    public String getSourceName() {
        return sourceName;
    }

    public void onStatusChange(HashMap<String, String> status) {
        int id = Integer.parseInt(status.get(getSourceName()));
        if (mediaId != id) {
            getMediaList().update();
            int length = Integer.parseInt(status.get(getSourceName()+"length"));
            int timelength = -1;
            if (status.get(getSourceName()+"timelength") != null) {
                timelength = Integer.parseInt(
                        status.get(getSourceName()+"timelength"));
            }
            setDescription(length, timelength);
            mediaId = id;
        }
        setCurrentPlaying(status);

        if (hasPlayorder) {
            String value = status.get(getSourceName()+"playorder");
            if (!value.equals(podrList.getValue(podrList.getSelectedIndex()))) {
                for (int idx=0; idx<podrList.getItemCount(); idx++) {
                    if (value.equals(podrList.getValue(idx))) {
                        podrList.setSelectedIndex(idx);
                        break;
                    }
                }
            }
        }

        if (hasRepeat) {
            boolean value = Boolean.parseBoolean(
                    status.get(getSourceName()+"repeat"));
            if (repeatCk.getValue() != value) {
                repeatCk.setValue(value);
            }
        }

        customUpdate();
    }

    protected ListBox makePlayorderWidget() {
        podrList = new ListBox();
        podrList.addItem(ui.i18nConstants.inOrder(), "inorder");
        podrList.addItem(ui.i18nConstants.oneMedia(), "onemedia");
        podrList.addItem(ui.i18nConstants.random(), "random");
        podrList.addItem(ui.i18nConstants.weightedRandom(), "random-weighted");
        podrList.addChangeHandler(new ChangeHandler() {
            public void onChange(ChangeEvent event) {
                ListBox lb = (ListBox) event.getSource();
                ui.rpc.setOption(getSourceName(), "playorder",
                        lb.getValue(lb.getSelectedIndex()),
                        new DefaultRpcCallback(ui));
            }
        });

        return podrList;
    }

    protected Widget makeRepeatWidget() {
        repeatCk = new CheckBox(ui.i18nConstants.repeat());
        repeatCk.addClickHandler(new ClickHandler() {
            public void onClick(ClickEvent event) {
                ui.rpc.setOption(getSourceName(), "repeat",
                        repeatCk.getValue(), new DefaultRpcCallback(ui));
            }
        });

        return repeatCk;
    }

    public void setCurrentPlaying(HashMap<String, String> status) {
        String state = status.get("state");
        if (!state.equals("stop")) {
            String current = status.get("current");
            String[] currentArray = current.split(":");
            if (currentArray[2].equals(getSourceName())) {
                int pos = Integer.parseInt(currentArray[0]);
                if (currentPlayingPos != pos) {
                    resetCurrentPlaying();
                    getMediaList().setPlaying(pos);
                    currentPlayingPos = pos;
                }
            } else {
                resetCurrentPlaying();
            }
        } else {
            resetCurrentPlaying();
        }
    }

    public void resetCurrentPlaying() {
        if (currentPlayingPos != -1) {
            getMediaList().resetPlaying(currentPlayingPos);
            currentPlayingPos = -1;
        }
    }

    /*
     * Abstract methods
     */
    abstract protected void customUpdate();
    abstract public MediaList getMediaList();
    abstract protected void setDescription(int length, int timelength);
}

//vim: ts=4 sw=4 expandtab