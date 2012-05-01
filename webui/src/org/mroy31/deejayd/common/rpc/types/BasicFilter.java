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

import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;

public class BasicFilter extends MediaFilter {
    private String id;
    private String tag;
    private String pattern;

    public BasicFilter(String id, String tag, String pattern) {
        this.id = id;
        this.tag = tag;
        this.pattern = pattern;
    }

    @Override
    public boolean equals(MediaFilter filter) {
        if (filter.getType() == "basic" && filter.getId() == id) {
            BasicFilter bFilter = filter.isBasic();
            return (bFilter.getTag() == tag && bFilter.getPattern() == pattern);
        }
        return false;
    }

    @Override
    public String getType() {
        return "basic";
    }

    @Override
    public String getId() {
        return id;
    }

    public String getTag() {
        return tag;
    }

    public void setTag(String tag) {
    	this.tag = tag;
    }
    
    public String getPattern() {
        return pattern;
    }

    public void setPattern(String pattern) {
    	this.pattern = pattern;
    }
    
    @Override
    public BasicFilter isBasic() {
        return this;
    }

    @Override
    public ComplexFilter isComplex() {
        return null;
    }

    @Override
    public JSONObject toJSON() {
        JSONObject filterObj = super.toJSON();
        JSONObject value = new JSONObject();
        value.put("tag", new JSONString(tag));
        value.put("pattern", new JSONString(pattern));
        filterObj.put("value", value);
        return filterObj;
    }

}

//vim: ts=4 sw=4 expandtab