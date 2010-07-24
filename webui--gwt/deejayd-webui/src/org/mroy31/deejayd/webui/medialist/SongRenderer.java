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

import org.mroy31.deejayd.common.widgets.DeejaydUtils;
import org.mroy31.deejayd.webui.client.WebuiLayout;
import org.mroy31.deejayd.webui.events.DragStartEvent;
import org.mroy31.deejayd.webui.events.DragStartHandler;
import org.mroy31.deejayd.webui.events.HasDragHandlers;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.resources.client.ImageResource;
import com.google.gwt.user.client.DOM;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.FlexTable;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;

public class SongRenderer extends MediaListRenderer implements DragStartHandler {

    public class GrippyWidget extends Image implements HasDragHandlers {
        private int row;
        private String mediaId;
        private String sourceId;

        public GrippyWidget(ImageResource img, int row, String id, String mId) {
            super(img);
            this.row = row;
            this.sourceId = id;
            this.mediaId = mId;

            getElement().setAttribute("draggable", "true");
            DOM.setStyleAttribute(getElement(), "margin", "0px 3px");
            DOM.setStyleAttribute(getElement(), "cursor", "move");
        }

        @Override
        public HandlerRegistration addDragStartHandler(DragStartHandler handler) {
            return addDomHandler(handler, DragStartEvent.getType());
        }

        public int getRow() {
            return row;
        }

        public String getSourceId() {
            return sourceId;
        }

        public String getMediaId() {
            return mediaId;
        }
    }

    public SongRenderer(WebuiLayout webui, String source, Label loadZone) {
        super(webui, source, loadZone);
    }

    @Override
    public void formatHeader(FlexTable header, final MediaList mediaList) {
        header.getColumnFormatter().setWidth(0, "10px"); // grippy
        header.getColumnFormatter().setWidth(1, "28px"); // checkbox
        header.getColumnFormatter().setWidth(2, "18px"); // play button
        header.getColumnFormatter().setWidth(3, "40px"); // tracknumber
        header.getFlexCellFormatter().setColSpan(0, 4, 2); // title
        header.getColumnFormatter().setWidth(9, "50px"); // length
        header.getColumnFormatter().setWidth(10, "65px"); // rating

        // add a checkbox
        final CheckBox allCk = new CheckBox();
        allCk.addClickHandler(new ClickHandler() {
            public void onClick(ClickEvent event) {
                boolean value = allCk.getValue();
                mediaList.checkRow(value);
            }
        });
        header.setWidget(0, 1, allCk);
        // set other columns
        header.setText(0, 3, "#");
        header.setText(0, 4, ui.i18nConstants.title());
        header.setText(0, 5, ui.i18nConstants.artist());
        header.setText(0, 6, ui.i18nConstants.album());
        header.setText(0, 7, ui.i18nConstants.genre());
        header.setText(0, 8, ui.i18nConstants.length());
        header.setText(0, 9, ui.i18nConstants.rating());
    }

    @Override
    public void formatMediaList(FlexTable mediaList) {
        mediaList.getColumnFormatter().setWidth(0, "10px"); // grippy
        mediaList.getColumnFormatter().setWidth(1, "28px"); // checkbox
        mediaList.getColumnFormatter().setWidth(2, "18px"); // play button
        mediaList.getColumnFormatter().setWidth(3, "40px"); // tracknumber
        mediaList.getColumnFormatter().setWidth(9, "50px"); // length
        mediaList.getColumnFormatter().setWidth(10, "65px"); // rating
    }

    @Override
    public void formatRow(int idx, FlexTable list, JSONObject media) {
        int id = (int) media.get("id").isNumber().doubleValue();
        int mId = (int) media.get("media_id").isNumber().doubleValue();

        // add a grippy
        GrippyWidget grippy = new GrippyWidget(ui.resources.drag(), idx,
                Integer.toString(id), Integer.toString(mId));
        grippy.addDragStartHandler(this);
        list.setWidget(idx, 0, grippy);

        // add a checkbox
        CheckBox checkbox = new CheckBox();
        checkbox.setFormValue(Integer.toString(id));
        list.setWidget(idx, 1, checkbox);

        list.setWidget(idx, 2, getPlayButton(id));
        list.setText(idx, 3, media.get("tracknumber")
                                       .isString().stringValue());
        list.getFlexCellFormatter().setColSpan(idx, 4, 2); // title
        list.setWidget(idx, 4, formatTagCell(media, "title"));
        list.setWidget(idx, 5, formatTagCell(media, "artist"));
        list.setWidget(idx, 6, formatTagCell(media, "album"));
        list.setWidget(idx, 7, formatTagCell(media, "genre"));

        // set medialength
        int length = Integer.parseInt(media.get("length").
                isString().stringValue());
        list.setText(idx, 8, DeejaydUtils.formatTime(length));

        // set rating
        list.setWidget(idx, 9, makeRatingWidget(media));
    }

    @Override
    public int getCkColumn() {
        return 1;
    }

    @Override
    public void onDragStart(DragStartEvent event) {
        GrippyWidget gWidget = (GrippyWidget) event.getSource();
        event.dataTransfert().setData(source+"-"+gWidget.getSourceId()+"-"+
                gWidget.getMediaId());

        mediaList.checkRow(false);
        mediaList.checkRow(gWidget.getRow(), true);
    }
}

//vim: ts=4 sw=4 expandtab