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

import java.util.ArrayList;

import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;

public class ComplexFilter extends MediaFilter {
    private String id;
    private ArrayList<MediaFilter> filterList = new ArrayList<MediaFilter>();

    public ComplexFilter(String id) {
        this.id = id;
    }

    public void addFilter(MediaFilter filter) {
        filterList.add(filter);
    }

    public MediaFilter[] getFilters() {
        return filterList.toArray(new MediaFilter[0]);
    }

    public boolean containsFilter(MediaFilter filter) {
        for (int idx=0; idx<filterList.size(); idx++) {
            if (filterList.get(idx).equals(filter))
                return true;
        }
        return false;
    }

    @Override
    public boolean equals(MediaFilter filter) {
        if (filter.getType() == "complex" && filter.getId() == id) {
            MediaFilter[] fList = filter.isComplex().getFilters();
            if (fList.length == filterList.size()) {
                for (int idx=0; idx<fList.length; idx++) {
                    if (!containsFilter(fList[idx]))
                        return false;
                }
                return true;
            }
        }
        return false;
    }

    @Override
    public ComplexFilter isComplex() {
        return this;
    }
    @Override
    public BasicFilter isBasic() {
        return null;
    }

    @Override
    public String getId() {
        return id;
    }

    @Override
    public String getType() {
        return "complex";
    }

    @Override
    public JSONObject toJSON() {
        JSONObject filterObj = super.toJSON();
        JSONArray value = new JSONArray();
        for (int idx=0; idx<filterList.size(); idx++) {
            value.set(idx, filterList.get(idx).toJSON());
        }
        filterObj.put("value", value);
        return filterObj;
    }
}

//vim: ts=4 sw=4 expandtab