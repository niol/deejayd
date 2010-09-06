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

import org.mroy31.deejayd.webui.client.WebuiLayout;
import org.mroy31.deejayd.webui.widgets.RatingWidget;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.user.client.ui.FlexTable;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;

public abstract class MediaListRenderer {
    protected WebuiLayout ui;
    protected String source;
    protected Label loadZoneLabel;
    protected MediaList mediaList;

    /**
     * Handler to update rating of a media
     *
     */
    protected ValueChangeHandler<Integer> ratingHandler =
        new ValueChangeHandler<Integer>() {
            public void onValueChange(ValueChangeEvent<Integer> event) {
                RatingWidget source = (RatingWidget) event.getSource();
                int[] ids = {source.getMediaId()};
                ui.rpc.setRating(ids, event.getValue(), null);
            }
    };

    /**
     * Click Handler to play a specific media
     */
    protected class PlayRowHandler implements ClickHandler {
        private int id;

        public PlayRowHandler(int id) {
            this.id = id;
        }

        public void onClick(ClickEvent event) {
            ui.rpc.goTo(id, source, null);
        }
    }

    /**
     * MediaListRenderer constructor
     */
    public MediaListRenderer(WebuiLayout webui, String source, Label loadZone) {
        this.ui = webui;
        this.source = source;
        this.loadZoneLabel = loadZone;
    }

    public void setMediaListParent(MediaList list) {
        this.mediaList = list;
    }

    public void setLoadText(String text) {
        if (loadZoneLabel != null)
            loadZoneLabel.setText(text);
    }

    protected Image getPlayButton(int id) {
        Image playButton = new Image(ui.resources.medialistPlay());
        playButton.addClickHandler(new PlayRowHandler(id));

        return playButton;
    }

    protected RatingWidget makeRatingWidget(JSONObject media) {
        int mediaId = (int) media.get("media_id").isNumber().doubleValue();
        int rating = Integer.parseInt(media.get("rating").
                isString().stringValue());
        RatingWidget rWidget = new RatingWidget(rating, mediaId, ui.resources);
        rWidget.addValueChangeHandler(ratingHandler);

        return rWidget;
    }


    protected Label formatTagCell(JSONObject media, String tag) {
        Label label = new Label(media.get(tag).isString().stringValue());
        label.addStyleName(ui.resources.webuiCss().textOverflow());

        return label;
    }

    public int getCkColumn() {
        return 0;
    }

    public abstract void formatHeader(FlexTable header, MediaList mediaList);
    public abstract void formatMediaList(FlexTable mediaList);
    public abstract void formatRow(int idx, FlexTable mediaList, JSONObject m);
}

//vim: ts=4 sw=4 expandtab