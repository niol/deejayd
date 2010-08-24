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

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.FlexTable;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;

public class WebradioRenderer extends MediaListRenderer {

    public WebradioRenderer(WebuiLayout webui, String source, Label loadZone) {
        super(webui, source, loadZone);
    }

    @Override
    public void formatHeader(FlexTable header, final MediaList mediaList) {
        header.getColumnFormatter().setWidth(0, "28px"); // checkbox
        header.getColumnFormatter().setWidth(1, "18px"); // play button

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
        header.setText(0, 2, ui.i18nConstants.title());
        header.setText(0, 3, ui.i18nConstants.url());
    }

    @Override
    public void formatMediaList(FlexTable mediaList) {
        mediaList.getColumnFormatter().setWidth(0, "28px"); // checkbox
        mediaList.getColumnFormatter().setWidth(1, "18px"); // play button
    }

    @Override
    public void formatRow(int idx, FlexTable list, JSONObject media) {
        int id = (int) media.get("id").isNumber().doubleValue();

        // add a checkbox
        CheckBox checkbox = new CheckBox();
        checkbox.setFormValue(Integer.toString(id));
        list.setWidget(idx, 0, checkbox);

        Image playButton = new Image(ui.resources.medialistPlay());
        playButton.addClickHandler(new PlayRowHandler(id));
        list.setWidget(idx, 1, playButton);

        list.setWidget(idx, 2, formatTagCell(media, "title"));
        String urlType = media.get("url-type").isString().stringValue();
        String value = "";
        if (urlType.equals("pls")) {
            value = media.get("url").isString().stringValue();
        } else if (urlType.equals("urls")) {
            JSONArray urls = media.get("urls").isArray();
            for (int i=0; i<urls.size(); i++) {
                value += urls.get(i).isString().stringValue()+"<br/>";
            }
        }
        HTML urlLabel = new HTML(value);
        urlLabel.addStyleName(ui.resources.webuiCss().textOverflow());
        list.setWidget(idx, 3, urlLabel);
    }

}

//vim: ts=4 sw=4 expandtab