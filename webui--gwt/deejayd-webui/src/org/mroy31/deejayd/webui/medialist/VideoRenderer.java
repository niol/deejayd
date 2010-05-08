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

import com.google.gwt.json.client.JSONObject;
import com.google.gwt.user.client.ui.FlexTable;
import com.google.gwt.user.client.ui.Label;

public class VideoRenderer extends MediaListRenderer {

    public VideoRenderer(WebuiLayout webui, String source, Label loadZone) {
        super(webui, source, loadZone);
    }

    @Override
    public void formatHeader(FlexTable header, MediaList mediaList) {
        header.getColumnFormatter().setWidth(0, "18px"); // play button
        header.getColumnFormatter().setWidth(2, "40px"); // width
        header.getColumnFormatter().setWidth(3, "40px"); // height
        header.getColumnFormatter().setWidth(4, "50px"); // length
        header.getColumnFormatter().setWidth(5, "50px"); // subtitles
        header.getColumnFormatter().setWidth(6, "65px"); // rating

        header.setText(0, 1, ui.i18nConstants.title());
        header.setText(0, 2, ui.i18nConstants.width());
        header.setText(0, 3, ui.i18nConstants.height());
        header.setText(0, 4, ui.i18nConstants.length());
        header.setText(0, 5, ui.i18nConstants.subtitle());
        header.setText(0, 6, ui.i18nConstants.rating());
    }

    @Override
    public void formatMediaList(FlexTable mediaList) {
        mediaList.getColumnFormatter().setWidth(0, "18px"); // play button
        mediaList.getColumnFormatter().setWidth(2, "40px"); // width
        mediaList.getColumnFormatter().setWidth(3, "40px"); // height
        mediaList.getColumnFormatter().setWidth(4, "50px"); // length
        mediaList.getColumnFormatter().setWidth(5, "50px"); // subtitles
        mediaList.getColumnFormatter().setWidth(6, "65px"); // rating
    }

    @Override
    public void formatRow(int idx, FlexTable list, JSONObject media) {
        int id = (int) media.get("id").isNumber().doubleValue();

        list.setWidget(idx, 0, getPlayButton(id));
        list.setWidget(idx, 1,formatTagCell(media, "title"));
        list.setWidget(idx, 2, formatTagCell(media, "videowidth"));
        list.setWidget(idx, 3, formatTagCell(media, "videoheight"));
        String sub = media.get("subtitle").isString().stringValue();
        list.setText(idx, 5, (sub.equals("") ? "no" : "yes"));

        // set medialength
        int l = Integer.parseInt(media.get("length").isString().stringValue());
        list.setText(idx, 4, DeejaydUtils.formatTime(l));

        // set rating
        list.setWidget(idx, 6, makeRatingWidget(media));
    }

}

//vim: ts=4 sw=4 expandtab