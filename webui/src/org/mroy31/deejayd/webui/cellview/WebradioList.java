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

package org.mroy31.deejayd.webui.cellview;

import org.mroy31.deejayd.common.rpc.types.Media;
import org.mroy31.deejayd.webui.cellview.columns.MediaAttrColumn;
import org.mroy31.deejayd.webui.client.WebuiLayout;

import com.google.gwt.cell.client.TextCell;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.user.cellview.client.Column;
import com.google.gwt.user.client.ui.Label;

public class WebradioList extends AbstractMediaList {

    public WebradioList(final WebuiLayout ui) {
        super(ui, "webradio", DEFAULT_PAGE_SIZE, true);

        addSelectionColumn();
        addColumn(new MediaAttrColumn("title", ui),
                new Label(ui.i18nConstants.title()), 2);
        addColumn(new Column<Media, String>(new TextCell()) {

            @Override
            public String getValue(Media object) {
                String urlType = object.getStrAttr("url-type");
                String value = "";
                if (urlType.equals("pls")) {
                    value = object.getStrAttr("url");
                } else if (urlType.equals("urls")) {
                    JSONArray urls = object.getArrayAttr("urls");
                    if (urls.size() == 1)
                        value = urls.get(0).isString().stringValue();
                    else
                        value=ui.i18nMessages.urlCount(urls.size());
                }
                return value;
            }
        }, new Label(ui.i18nConstants.url()), 2);
    }

}

//vim: ts=4 sw=4 expandtab