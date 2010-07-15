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

package org.mroy31.deejayd.mobile.sources;

import com.google.gwt.json.client.JSONObject;
import com.google.gwt.user.client.ui.Widget;


public class WebradioMode extends DefaultDeejaydMode {

    public WebradioMode() {
        super("webradio");
    }

    @Override
    public MediaList initMediaList() {
        return new MediaList("webradio", new MediaListFormater() {
            @Override
            public Widget formatRow(JSONObject media) {
                String title = media.get("title").isString().stringValue();
                return new MediaItem(
                        (int) media.get("id").isNumber().doubleValue(),
                        title, "");
            }
        });
    }

    @Override
    public String getTitle() {
        return ui.i18nConst.webradio();
    }
}

//vim: ts=4 sw=4 expandtab