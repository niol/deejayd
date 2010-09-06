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
import java.util.List;

import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;

public class FileDirList {
    private final JSONObject fileDirList;
    private ArrayList<String> directories;
    private ArrayList<Media> files;

    public FileDirList(JSONObject answer) {
        this.fileDirList = answer;
    }

    public List<String> getDirectories() {
        if (directories == null) {
            JSONArray list  = this.fileDirList.get("directories").isArray();
            directories = new ArrayList<String>();

            for (int idx=0; idx<list.size(); idx++)
                directories.add(list.get(idx).isString().stringValue());
        }
        return directories;
    }

    public List<Media> getFiles() {
        if (files == null) {
            JSONArray list  = this.fileDirList.get("files").isArray();
            files = new ArrayList<Media>();

            for (int idx=0; idx<list.size(); idx++)
                files.add(new Media(list.get(idx).isObject()));
        }
        return files;
    }

    public String getRootPath() {
        return fileDirList.get("root").isString().stringValue();
    }
}

//vim: ts=4 sw=4 expandtab