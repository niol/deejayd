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

import java.util.AbstractList;
import java.util.List;

import com.google.gwt.json.client.JSONArray;


public class MediaList {
    private JSONArray mediaList;
    private MediaFilter filter;
    private MediaListSort sort;

    public void setMediaList(JSONArray list) {
        this.mediaList = list;
    }

    public void setFilter(MediaFilter filter) {
        this.filter = filter;
    }

    public void setSort(MediaListSort sort) {
        this.sort = sort;
    }

    public List<Media> getMediaList() {
        return new AbstractList<Media>() {

            @Override
            public Media get(int index) {
                return new Media(mediaList.get(index).isObject());
            }

            @Override
            public int size() {
                return mediaList.size();
            }
        };
    }

    public MediaFilter getFilter() {
        return filter;
    }

    public MediaListSort getSort() {
        return sort;
    }
}

//vim: ts=4 sw=4 expandtab