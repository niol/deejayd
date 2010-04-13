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

package org.mroy31.deejayd.webui.medialist;

import java.util.ArrayList;

import org.mroy31.deejayd.common.rpc.GenericRpcCallback;
import org.mroy31.deejayd.common.rpc.MediaFilter;
import org.mroy31.deejayd.webui.client.WebuiLayout;
import org.mroy31.deejayd.webui.resources.WebuiResources;

import com.google.gwt.core.client.GWT;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.DeferredCommand;
import com.google.gwt.user.client.IncrementalCommand;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.FlexTable;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.ScrollPanel;
import com.google.gwt.user.client.ui.Widget;

public class MediaList extends Composite {

    private static MediaListUiBinder uiBinder = GWT
            .create(MediaListUiBinder.class);
    interface MediaListUiBinder extends UiBinder<Widget, MediaList> {}

    private WebuiLayout ui;
    private String source;
    private boolean hasSelection = false;
    private MediaListRenderer renderer;
    private MediaFilter filter;

    @UiField FlexTable header;
    @UiField FlexTable mediaList;
    @UiField ScrollPanel mediaListPanel;
    @UiField(provided = true) final WebuiResources resources;

    /**
     * Rpc callback used for source.get command
     *
     */
    private class MediaListCallback extends GenericRpcCallback {
        public MediaListCallback(WebuiLayout ui) {
            super(ui);
        }
        public void onCorrectAnswer(JSONValue data) {
            // record filter
            JSONObject filterObj = data.isObject().get("filter").isObject();
            if (filterObj != null)
                filter = MediaFilter.parse(filterObj);
            else
                filter = null;
            JSONArray list = data.isObject().get("medias").isArray();
            setMedia(list);
        }
    }

    /**
     * Incremental command to load media list
     *
     */
    private class MedialistUpdate implements IncrementalCommand {
        private int CHUNKLENGTH = 200;
        private int lastGet = 0;
        private JSONArray list;

        public MedialistUpdate(JSONArray list) {
            this.list = list;
        }

        public boolean execute() {
            for (int idx=0; idx<CHUNKLENGTH; idx++) {
                if (lastGet < list.size()) {
                    // set style for this row
                    if ((lastGet % 2) == 0) {
                        mediaList.getRowFormatter().setStyleName(idx,
                                resources.webuiCss().oddRow());
                    }
                    renderer.formatRow(lastGet, mediaList,
                            list.get(lastGet).isObject());
                    lastGet++;
                } else {
                    return false;
                }
            }
            return true;
        }
    }

    /**
     * MediaList constructor
     * @param webui
     */
    public MediaList(WebuiLayout webui, String source) {
        this.source = source;
        this.ui= webui;
        this.resources = webui.resources;

        initWidget(uiBinder.createAndBindUi(this));
    }

    public void setOption(boolean hasSelection, MediaListRenderer r) {
        this.renderer = r;
        this.hasSelection = hasSelection;

        renderer.formatHeader(header, this);
        renderer.formatMediaList(mediaList);
    }

    public void update() {
        mediaList.removeAllRows();
        mediaList.setWidget(0, 0, new Image(resources.loading()));
        mediaList.setText(0, 2, ui.i18nConstants.loading());
        ui.rpc.send(source+".get", new JSONArray(), new MediaListCallback(ui));
    }

    public void setMedia(JSONArray list) {
        mediaList.removeAllRows();
        DeferredCommand.addCommand(new MedialistUpdate(list));
    }

    public void goTo(int pos) {
        Widget wg = mediaList.getWidget(pos, 0);
        mediaListPanel.ensureVisible(wg);
    }

    public void checkRow(boolean value) {
        int size = mediaList.getRowCount();
        for (int idx=0; idx<size; idx++) {
            CheckBox ck = (CheckBox) mediaList.getWidget(idx, 0);
            ck.setValue(value);
        }
    }

    public MediaFilter getFilter() {
        return filter;
    }

    public String[] getSelection() {
        if (hasSelection) {
            ArrayList<String> selection = new ArrayList<String>();
            for (int idx=0; idx<mediaList.getRowCount(); idx++) {
                CheckBox ck = (CheckBox) mediaList.getWidget(idx, 0);
                if (ck.getValue())
                    selection.add(ck.getFormValue());
            }
            String[] result = new String[0];
            return selection.toArray(result);
        }
        return null;
    }

    public void setPlaying(int pos) {
        mediaList.getRowFormatter().addStyleName(pos,
                resources.webuiCss().currentItem());
    }

    public void resetPlaying(int pos) {
        mediaList.getRowFormatter().removeStyleName(pos,
                resources.webuiCss().currentItem());
    }
}

//vim: ts=4 sw=4 expandtab