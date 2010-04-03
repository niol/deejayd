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

import org.mroy31.deejayd.common.rpc.DefaultRpcCallback;
import org.mroy31.deejayd.common.widgets.DeejaydUtils;
import org.mroy31.deejayd.webui.resources.WebuiResources;
import org.mroy31.deejayd.webui.widgets.RatingWidget;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.DeferredCommand;
import com.google.gwt.user.client.IncrementalCommand;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.FlexTable;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Widget;

public class QueueMediaList extends Composite {
    private WebuiLayout ui;

    private static QueueMediaListUiBinder uiBinder = GWT
            .create(QueueMediaListUiBinder.class);
    interface QueueMediaListUiBinder extends UiBinder<Widget, QueueMediaList> {}

    @UiField FlexTable header;
    @UiField FlexTable mediaList;
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
     * Click Handler to play a specific media
     */
    protected class PlayRowHandler implements ClickHandler {
        private int id;

        public PlayRowHandler(int id) {
            this.id = id;
        }

        @Override
        public void onClick(ClickEvent event) {
            ui.rpc.goTo(id, "queue", new DefaultRpcCallback(ui));
        }
    }

    /**
     * Incremental command to load media list
     *
     */
    private class MedialistUpdate implements IncrementalCommand {
        private int CHUNKLENGTH = 500;
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
                    buildRow(lastGet, mediaList, list.get(lastGet).isObject());

                    lastGet++;
                } else {
                    return false;
                }
            }
            return true;
        }
    }

    /**
     * QueueMediaList contructor
     * @param webui
     */

    public QueueMediaList(WebuiLayout webui) {
        ui = webui;
        this.resources = ui.resources;

        initWidget(uiBinder.createAndBindUi(this));
        buildHeader();
        formatMediaList(mediaList);
    }

    public void setLoading() {
        mediaList.removeAllRows();
        mediaList.setWidget(0, 0, new Image(resources.loading()));
        mediaList.setText(0, 2, ui.i18nConstants.loading());
    }

    public void checkRow(boolean value) {
        int size = mediaList.getRowCount();
        for (int idx=0; idx<size; idx++) {
            CheckBox ck = (CheckBox) mediaList.getWidget(idx, 0);
            ck.setValue(value);
        }
    }

    public String[] getSelection() {
        ArrayList<String> selection = new ArrayList<String>();
        for (int idx=0; idx<mediaList.getRowCount(); idx++) {
            CheckBox ck = (CheckBox) mediaList.getWidget(idx, 0);
            if (ck.getValue())
                selection.add(ck.getFormValue());
        }
        String[] result = new String[0];
        return selection.toArray(result);
    }

    private void buildHeader() {
        header.getColumnFormatter().setWidth(0, "28px"); // checkbox
        header.getColumnFormatter().setWidth(1, "18px"); // play button
        header.getColumnFormatter().setWidth(2, "40px"); // tracknumber
        header.getFlexCellFormatter().setColSpan(0, 3, 2); // title
        header.getColumnFormatter().setWidth(8, "50px"); // length
        header.getColumnFormatter().setWidth(9, "65px"); // rating

        // add a checkbox
        final CheckBox allCk = new CheckBox();
        allCk.addClickHandler(new ClickHandler() {
            public void onClick(ClickEvent event) {
                boolean value = allCk.getValue();
                checkRow(value);
            }
        });
        header.setWidget(0, 0, allCk);
        // set other columns
        header.setText(0, 2, "#");
        header.setText(0, 3, ui.i18nConstants.title());
        header.setText(0, 4, ui.i18nConstants.artist());
        header.setText(0, 5, ui.i18nConstants.album());
        header.setText(0, 6, ui.i18nConstants.genre());
        header.setText(0, 7, ui.i18nConstants.length());
        header.setText(0, 8, ui.i18nConstants.rating());
    }

    public void buildRow(int idx, FlexTable list, JSONObject media) {
        int id = (int) media.get("id").isNumber().doubleValue();

        // add a checkbox
        CheckBox checkbox = new CheckBox();
        checkbox.setFormValue(Integer.toString(id));
        list.setWidget(idx, 0, checkbox);

        Image playButton = new Image(resources.medialistPlay());
        playButton.addClickHandler(new PlayRowHandler(id));
        list.setWidget(idx, 1, playButton);

        list.setText(idx, 2, media.get("tracknumber")
                                       .isString().stringValue());
        list.getFlexCellFormatter().setColSpan(idx, 3, 2); // title
        list.setText(idx, 3, media.get("title").isString().stringValue());
        list.setText(idx, 4, media.get("artist").isString().stringValue());
        list.setText(idx, 5, media.get("album").isString().stringValue());
        list.setText(idx, 6, media.get("genre").isString().stringValue());

        // set medialength
        int length = Integer.parseInt(media.get("length").
                isString().stringValue());
        list.setText(idx, 7, DeejaydUtils.formatTime(length));

        // set rating
        list.setWidget(idx, 8, makeRatingWidget(media));
    }

    public void formatMediaList(FlexTable mediaList) {
        mediaList.getColumnFormatter().setWidth(0, "28px"); // checkbox
        mediaList.getColumnFormatter().setWidth(1, "18px"); // play button
        mediaList.getColumnFormatter().setWidth(2, "40px"); // tracknumber
        mediaList.getColumnFormatter().setWidth(8, "50px"); // length
        mediaList.getColumnFormatter().setWidth(9, "65px"); // rating
    }

    public void update(JSONArray list) {
        mediaList.removeAllRows();
        DeferredCommand.addCommand(new MedialistUpdate(list));
    }

    protected RatingWidget makeRatingWidget(JSONObject media) {
        int mediaId = (int) media.get("media_id").isNumber().doubleValue();
        int rating = Integer.parseInt(media.get("rating").
                isString().stringValue());
        RatingWidget rWidget = new RatingWidget(rating, resources);
        rWidget.addValueChangeHandler(new RatingChangeHandler(mediaId));

        return rWidget;
    }
}

//vim: ts=4 sw=4 expandtab