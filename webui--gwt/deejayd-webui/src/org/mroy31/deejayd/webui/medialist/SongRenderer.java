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

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.FlexTable;

public class SongRenderer extends MediaListRenderer {

    public SongRenderer(WebuiLayout webui, String source) {
        super(webui, source);
    }

    @Override
    public void formatHeader(FlexTable header, final MediaList mediaList) {
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
                mediaList.checkRow(value);
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

    @Override
    public void formatMediaList(FlexTable mediaList) {
        mediaList.getColumnFormatter().setWidth(0, "28px"); // checkbox
        mediaList.getColumnFormatter().setWidth(1, "18px"); // play button
        mediaList.getColumnFormatter().setWidth(2, "40px"); // tracknumber
        mediaList.getColumnFormatter().setWidth(8, "50px"); // length
        mediaList.getColumnFormatter().setWidth(9, "65px"); // rating
    }

    @Override
    public void formatRow(int idx, FlexTable list, JSONObject media) {
        int id = (int) media.get("id").isNumber().doubleValue();

        // add a checkbox
        CheckBox checkbox = new CheckBox();
        checkbox.setFormValue(Integer.toString(id));
        list.setWidget(idx, 0, checkbox);

        list.setWidget(idx, 1, getPlayButton(id));
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

}

//vim: ts=4 sw=4 expandtab