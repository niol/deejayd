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

import java.util.ArrayList;

import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONString;

public class MediaListSort {
    public static class TagSort {
        private final String tag;
        private final String value;

        public TagSort(String tag, String value) {
            this.tag = tag;
            this.value = value;
        }

        public String getTag() {
            return this.tag;
        }

        public String getValue() {
            return this.value;
        }
    }

    private ArrayList<TagSort> sortList = new ArrayList<TagSort>();

    public static MediaListSort parse(JSONArray sortObject) {
        MediaListSort ans = new MediaListSort();
        for (int idx=0; idx<sortObject.size(); idx++) {
            JSONArray item = sortObject.get(idx).isArray();
            ans.add(new TagSort(item.get(0).isString().stringValue(),
                    item.get(1).isString().stringValue()));
        }

        return ans;
    }

    public void add(TagSort sort) {
        sortList.add(sort);
    }

    public ArrayList<TagSort> getList() {
        return sortList;
    }

    public JSONArray toJSON() {
        JSONArray array = new JSONArray();
        for (TagSort item : sortList) {
            JSONArray sort = new JSONArray();
            sort.set(0, new JSONString(item.getTag()));
            sort.set(1, new JSONString(item.getValue()));

            array.set(array.size(), sort);
        }
        return array;
    }
}

//vim: ts=4 sw=4 expandtab