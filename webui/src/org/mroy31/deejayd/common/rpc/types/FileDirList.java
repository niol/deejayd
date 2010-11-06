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
import com.google.gwt.json.client.JSONObject;

public class FileDirList {
    private final JSONObject fileDirList;

    public FileDirList(JSONObject answer) {
        this.fileDirList = answer;
    }

    public List<String> getDirectories() {
        return new AbstractList<String>() {

            @Override
            public String get(int index) {
                return fileDirList.get("directories").isArray().get(index)
                        .isString().stringValue();
            }

            @Override
            public int size() {
                return fileDirList.get("directories").isArray().size();
            }
        };
    }

    public List<Media> getFiles() {
        return new AbstractList<Media>() {
            JSONArray list  = fileDirList.get("files").isArray();

            @Override
            public Media get(int index) {
                return new Media(list.get(index).isObject());
            }

            @Override
            public int size() {
                return list.size();
            }
        };
    }

    public String getRootPath() {
        return fileDirList.get("root").isString().stringValue();
    }
}

//vim: ts=4 sw=4 expandtab