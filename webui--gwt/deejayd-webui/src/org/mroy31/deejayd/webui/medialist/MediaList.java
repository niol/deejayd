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
import com.google.gwt.event.dom.client.ScrollEvent;
import com.google.gwt.event.dom.client.ScrollHandler;
import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.Command;
import com.google.gwt.user.client.DeferredCommand;
import com.google.gwt.user.client.IncrementalCommand;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.FlexTable;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.ScrollPanel;
import com.google.gwt.user.client.ui.Widget;

public class MediaList extends Composite {
    private final int PAGE_SIZE = 100;

    private static MediaListUiBinder uiBinder = GWT
            .create(MediaListUiBinder.class);
    interface MediaListUiBinder extends UiBinder<Widget, MediaList> {}

    private WebuiLayout ui;
    private String source;
    private boolean hasSelection = false;
    private MediaListRenderer renderer;
    private MediaFilter filter;
    private JSONArray mediaListArray;
    private int lastMediaLoaded = 0;
    private int currentPlaying = -1;

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
     * Incremental command to load medialist
     *
     */
    private class MedialistUpdate implements IncrementalCommand {
        private final int CHUNK_SIZE = 500;
        private Command onFinish;
        private int lastItem;
        private int currentItem = lastMediaLoaded;

        public MedialistUpdate(int lastItem, Command cmd) {
            this.lastItem = lastItem;
            this.onFinish = cmd;
        }

        @Override
        public boolean execute() {
            currentItem = Math.min(lastItem, currentItem+CHUNK_SIZE);
            for (int idx=lastMediaLoaded; idx<currentItem; idx++) {
                JSONObject media = mediaListArray.get(idx).isObject();
                // set style for this row
                if ((idx % 2) == 0)
                    mediaList.getRowFormatter().setStyleName(idx,
                            resources.webuiCss().oddRow());

                renderer.formatRow(idx, mediaList, media);
            }

            lastMediaLoaded = currentItem;
            renderer.setLoadText(
                    ui.i18nMessages.itemLoadedDesc(lastMediaLoaded,
                    mediaListArray.size()));
            if (currentItem == lastItem) {
                mScrollReg = mediaListPanel.addScrollHandler(mScrollHandler);
                if (currentPlaying != -1 && currentPlaying < lastItem)
                    mediaList.getRowFormatter().addStyleName(currentPlaying,
                            resources.webuiCss().currentItem());

                if (onFinish != null)
                    onFinish.execute();
                return false;
            }
            return true;
        }
    }

    /**
     * Medialist scroll handler
     */
    private ScrollHandler mScrollHandler = new ScrollHandler() {

        @Override
        public void onScroll(ScrollEvent event) {
            int height = mediaList.getOffsetHeight();
            int scrollPosition = mediaListPanel.getScrollPosition();
            if ((height - scrollPosition) < 750) {
                loadMediaList();
            }
        }
    };
    private HandlerRegistration mScrollReg;

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
        removeScrollHandler();

        mediaList.removeAllRows();
        mediaList.setWidget(0, 0, new Image(resources.loading()));
        mediaList.setText(0, 2, ui.i18nConstants.loading());
        ui.rpc.send(source+".get", new JSONArray(), new MediaListCallback(ui));
    }

    public void setMedia(JSONArray list) {
        renderer.setLoadText("");
        mediaList.removeAllRows();
        mediaListArray = list;
        lastMediaLoaded = 0;

        loadMediaList();
    }

    public void goTo(final int pos) {
        Command cmd =  new Command() {
            @Override
            public void execute() {
                Widget wg = mediaList.getWidget(pos, 0);
                mediaListPanel.ensureVisible(wg);
            }
        };

        if (pos < lastMediaLoaded)
            cmd.execute();
        else
            loadMediaList(pos+10, cmd);

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
        if (pos < lastMediaLoaded)
            mediaList.getRowFormatter().addStyleName(pos,
                    resources.webuiCss().currentItem());
        currentPlaying = pos;
    }

    public void resetPlaying(int pos) {
        if (pos < lastMediaLoaded)
            mediaList.getRowFormatter().removeStyleName(pos,
                    resources.webuiCss().currentItem());
        currentPlaying = -1;
    }

    private void loadMediaList() {
        loadMediaList(lastMediaLoaded+PAGE_SIZE);
    }

    private void loadMediaList(int lastItem) {
        loadMediaList(lastItem, null);
    }

    private void loadMediaList(int lastItem, Command onFinish) {
        removeScrollHandler();

        if (lastMediaLoaded < mediaListArray.size()) {
            renderer.setLoadText(ui.i18nConstants.loading());
            lastItem = Math.min(lastItem, mediaListArray.size());
            DeferredCommand.addCommand(new MedialistUpdate(lastItem, onFinish));

        }
    }

    private void removeScrollHandler() {
        if (mScrollReg != null) {
            mScrollReg.removeHandler();
            mScrollReg = null;
        }
    }
}

//vim: ts=4 sw=4 expandtab