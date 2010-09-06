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

package org.mroy31.deejayd.common.rpc.types;

import org.mroy31.deejayd.common.widgets.DeejaydUtils;

import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONValue;

public class Media {
    protected final JSONObject media;

    public Media(JSONObject media) {
        this.media = media;
    }

    public int getId() {
        return (int) media.get("id").isNumber().doubleValue();
    }

    public int getMediaId() {
        return (int) media.get("media_id").isNumber().doubleValue();
    }

    public String getTitle() {
        return media.get("title").isString().stringValue();
    }

    public String getStrAttr(String name) {
        if (media.get(name) != null) {
            JSONValue attr = media.get(name);
            if (attr.isString() != null) {
                return attr.isString().stringValue();
            } else if (attr.isNumber() != null) {
                return Integer.toString((int) attr.isNumber().doubleValue());
            } else if (attr.isBoolean() != null) {
                return Boolean.toString(attr.isBoolean().booleanValue());
            }
        }
        return null;
    }

    public int getIntAttr(String name) {
        if (media.get(name) != null) {
            JSONValue attr = media.get(name);
            if (attr.isString() != null) {
                return Integer.parseInt(attr.isString().stringValue());
            } else if (attr.isNumber() != null) {
                return (int) attr.isNumber().doubleValue();
            }
        }
        return -1;
    }

    public JSONArray getArrayAttr(String name) {
        if (media.containsKey(name)) {
            return media.get(name).isArray();
        }
        return null;
    }

    public boolean hasAttr(String name) {
        return media.containsKey(name);
    }

    public boolean isSong() {
        return media.get("type").isString().stringValue().equals("song");
    }

    public boolean isVideo() {
        return media.get("type").isString().stringValue().equals("video");
    }

    public boolean isWebradio() {
        return media.get("type").isString().stringValue().equals("webradio");
    }

    public String formatTitle() {
        String title = getTitle();
        if (isSong() || isVideo()) {
            title += " ("+DeejaydUtils.formatTime(getIntAttr("length"))+")";
        } else if (isWebradio()) {
            if (hasAttr("song-title"))
                title += " -- " + getStrAttr("song-title");
        }
        return title;
    }

    public String formatDesc() {
        String desc = "";
        if (isSong()) {
            if (hasAttr("artist"))
                desc += getStrAttr("artist");
            if (hasAttr("album"))
                desc += " - " + getStrAttr("album");
        } else if (isVideo()) {
            desc += getStrAttr("videowidth") + "x" + getStrAttr("videoheight");
        } else if (isWebradio()) {
            if (hasAttr("uri"))
                desc = getStrAttr("uri");
        }
        return desc;
    }
}

//vim: ts=4 sw=4 expandtab