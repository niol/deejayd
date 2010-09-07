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

package org.mroy31.deejayd.common.rpc.callbacks;

import java.util.ArrayList;

import org.mroy31.deejayd.common.rpc.types.Media;
import org.mroy31.deejayd.common.rpc.types.MediaFilter;
import org.mroy31.deejayd.common.rpc.types.MediaList;

import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONValue;

/**
 * callback from command who return a media list
 * @author Mickaël Royer
 *
 */
public class MediaListCallback extends AbstractRpcCallback {
    private final AnswerHandler<MediaList> handler;

    public MediaListCallback(AnswerHandler<MediaList> handler) {
        this.handler = handler;
    }

    @Override
    public void onCorrectAnswer(JSONValue data) {
        MediaList ans = new MediaList();

        ArrayList<Media> mList = new ArrayList<Media>();
        JSONArray list = data.isObject().get("medias").isArray();
        for (int idx=0; idx<list.size(); idx++)
            mList.add(new Media(list.get(idx).isObject()));
        ans.setMediaList(mList);

        JSONValue filter = data.isObject().get("filter");
        if (filter.isObject() != null)
            ans.setFilter(MediaFilter.parse(filter.isObject()));

        handler.onAnswer(ans);
    }

}

//vim: ts=4 sw=4 expandtab