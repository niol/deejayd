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

package org.mroy31.deejayd.common.rpc;

import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.json.client.JSONValue;

public abstract class MediaFilter {

    public static MediaFilter parse(JSONObject filterObj) {
        String id = filterObj.get("id").isString().stringValue();
        String type = filterObj.get("type").isString().stringValue();
        JSONValue value = filterObj.get("value");

        if (type.equals("basic")) {
            String tag = value.isObject().get("tag").isString().stringValue();
            String p = value.isObject().get("pattern").isString().stringValue();
            BasicFilter filter = new BasicFilter(id, tag, p);
            return filter;
        } else {
            ComplexFilter filter = new ComplexFilter(id);
            JSONArray list = value.isArray();
            for (int idx=0; idx<list.size(); idx++) {
                filter.addFilter(MediaFilter.parse(list.get(idx).isObject()));
            }
            return filter;
        }
    }

    public JSONObject toJSON() {
        JSONObject filterObj = new JSONObject();
        filterObj.put("id", new JSONString(getId()));
        filterObj.put("type", new JSONString(getType()));
        return filterObj;
    }

    abstract public boolean equals(MediaFilter filter);
    abstract public String getId();
    abstract public String getType();
    abstract public ComplexFilter isComplex();
    abstract public BasicFilter isBasic();
}

//vim: ts=4 sw=4 expandtab