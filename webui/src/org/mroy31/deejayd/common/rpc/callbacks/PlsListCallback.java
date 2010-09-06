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
import java.util.List;

import org.mroy31.deejayd.common.rpc.types.Playlist;

import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONValue;

public class PlsListCallback extends AbstractRpcCallback {
    private final AnswerHandler<List<Playlist>> handler;

    public PlsListCallback(AnswerHandler<List<Playlist>> handler) {
        this.handler = handler;
    }

    @Override
    public void onCorrectAnswer(JSONValue data) {
        ArrayList<Playlist> ans = new ArrayList<Playlist>();

        JSONArray list = data.isObject().get("medias").isArray();
        for (int idx=0; idx<list.size(); idx++)
            ans.add(new Playlist(list.get(idx).isObject()));
        handler.onAnswer(ans);
    }

}

//vim: ts=4 sw=4 expandtab