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

import java.util.ArrayList;
import java.util.HashMap;

import org.mroy31.deejayd.common.rpc.DefaultRpcCallback;
import org.mroy31.deejayd.common.rpc.GenericRpcCallback;
import org.mroy31.deejayd.common.widgets.IsLayoutWidget;
import org.mroy31.deejayd.webui.resources.WebuiResources;
import org.mroy31.deejayd.webui.widgets.RatingWidget;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ChangeEvent;
import com.google.gwt.event.dom.client.ChangeHandler;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONNumber;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.DeferredCommand;
import com.google.gwt.user.client.IncrementalCommand;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.FlexTable;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.ListBox;
import com.google.gwt.user.client.ui.ScrollPanel;
import com.google.gwt.user.client.ui.Widget;

public abstract class WebuiMode extends Composite {
    protected String sourceName;
    protected WebuiLayout ui;
    protected int mediaId = -1;
    protected int selectionLength = 0;
    protected int currentPlayingPos = -1;

    public boolean hasPlayorder;
    private ListBox podrList;
    public boolean hasRepeat;
    private CheckBox repeatCk;

    private static WebuiModeUiBinder uiBinder = GWT
            .create(WebuiModeUiBinder.class);
    interface WebuiModeUiBinder extends
        UiBinder<Widget, WebuiMode> {
    }

    @UiField FlexTable modeHeader;
    @UiField FlexTable modeMedialist;
    @UiField ScrollPanel modeMedialistPanel;
    @UiField HorizontalPanel modeTopToolbar;
    @UiField HorizontalPanel modeBottomToolbar;
    @UiField(provided = true) final WebuiResources resources;

    /**
     * Handler to update rating of a media
     *
     */
    class RatingChangeHandler implements ValueChangeHandler<Integer> {
        private int mediaId;
        public RatingChangeHandler(int mediaId) {
            this.mediaId = mediaId;
        }

        public void onValueChange(ValueChangeEvent<Integer> event) {
            int[] ids = new int[1];
            ids[0] = mediaId;
            ui.rpc.setRating(ids, event.getValue(),
                    new DefaultRpcCallback(ui));
        }
    }

    /**
     * Rpc callback used for source.get command
     *
     */
    private class MediaListCallback extends GenericRpcCallback {
        private int lastGet;
        public MediaListCallback(int lastGet, IsLayoutWidget ui) {
            super(ui);
            this.lastGet = lastGet;
        }
        public void onCorrectAnswer(JSONValue data) {
            JSONArray list = data.isObject().get("medias").isArray();
            for (int idx=0; idx<list.size(); idx++) {
                buildRow(modeMedialist, lastGet+idx, list.get(idx).isObject());
            }
        }
    }

    /**
     * Incremental command to load media list
     *
     */
    private class MedialistUpdate implements IncrementalCommand {
        private int CHUNKLENGTH = 100;
        private int lastGet = 0;
        private int length;
        private HashMap<String, String> status;

        public MedialistUpdate(int length, HashMap<String, String> status) {
            this.length = length;
            this.status = status;
        }

        public boolean execute() {
            JSONArray args = new JSONArray();
            args.set(0, new JSONNumber(lastGet));
            args.set(1, new JSONNumber(CHUNKLENGTH));
            ui.rpc.send(getSourceName()+".get",
                    args, new MediaListCallback(lastGet, ui));

            lastGet += CHUNKLENGTH;
            if (lastGet >= length) {
                setCurrentPlaying(status);
                return false;
            }
            return true;
        }
    }

    /**
     * Click Handler to play a specific media
     */
    protected class PlayRowHandler implements ClickHandler {
        private int id;

        public PlayRowHandler(int id) {
            this.id = id;
        }

        @Override
        public void onClick(ClickEvent event) {
            ui.rpc.goTo(id, new DefaultRpcCallback(ui));
        }
    }

    public WebuiMode(String source, WebuiLayout webui,
            boolean hasPlayorder, boolean hasRepeat) {
        this.ui = webui;
        this.resources = webui.resources;
        this.sourceName = source;
        this.hasPlayorder = hasPlayorder;
        this.hasRepeat = hasRepeat;

        initWidget(uiBinder.createAndBindUi(this));

        modeTopToolbar.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);
        modeBottomToolbar.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);
        buildBottomToolbar(modeBottomToolbar);
        buildTopToolbar(modeTopToolbar);
        buildHeader(modeHeader);
        formatMedialist(modeMedialist);
    }

    public String getSourceName() {
        return sourceName;
    }

    public void onStatusChange(HashMap<String, String> status) {
        int id = Integer.parseInt(status.get(getSourceName()));
        if (mediaId != id) {
            modeMedialist.removeAllRows();
            int length = Integer.parseInt(status.get(getSourceName()+"length"));
            int timelength = -1;
            if (status.get(getSourceName()+"timelength") != null) {
                timelength = Integer.parseInt(
                        status.get(getSourceName()+"timelength"));
            }
            DeferredCommand.addCommand(new MedialistUpdate(length, status));
            setDescription(length, timelength);
            mediaId = id;
            currentPlayingPos = -1;
        } else { // update current playing state if necessary
            setCurrentPlaying(status);
        }

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
    }

    protected RatingWidget makeRatingWidget(JSONObject media) {
        int mediaId = (int) media.get("media_id").isNumber().doubleValue();
        int rating = Integer.parseInt(media.get("rating").
                isString().stringValue());
        RatingWidget rWidget = new RatingWidget(rating, resources);
        rWidget.addValueChangeHandler(new RatingChangeHandler(mediaId));

        return rWidget;
    }

    protected ListBox makePlayorderWidget() {
        podrList = new ListBox();
        podrList.addItem(ui.i18nConstants.inOrder(), "inorder");
        podrList.addItem(ui.i18nConstants.oneMedia(), "onemedia");
        podrList.addItem(ui.i18nConstants.random(), "random");
        podrList.addItem(ui.i18nConstants.weightedRandom(),
                "random-weighted");
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

    protected String[] getMediaSelection() {
        ArrayList<String> selection = new ArrayList<String>();
        for (int idx=0; idx<modeMedialist.getRowCount(); idx++) {
            CheckBox ck = (CheckBox) modeMedialist.getWidget(idx, 0);
            if (ck.getValue())
                selection.add(ck.getFormValue());
        }
        String[] result = new String[0];
        return selection.toArray(result);
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
                    modeMedialist.getRowFormatter().addStyleName(pos,
                            resources.webuiCss().currentItem());
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
            modeMedialist.getRowFormatter().removeStyleName(currentPlayingPos,
                    resources.webuiCss().currentItem());
            currentPlayingPos = -1;
        }
    }

    /*
     * Abstract methods
     */
    abstract void buildTopToolbar(HorizontalPanel toolbar);
    abstract void buildBottomToolbar(HorizontalPanel toolbar);
    abstract void buildHeader(FlexTable header);
    abstract void formatMedialist(FlexTable mediaList);
    abstract void buildRow(FlexTable mediaList,	int idx, JSONObject media);
    abstract void setDescription(int length, int timelength);
}

//vim: ts=4 sw=4 expandtab