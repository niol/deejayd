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

import com.google.gwt.core.client.GWT;
import com.google.gwt.http.client.RequestBuilder;
import com.google.gwt.http.client.RequestException;
import com.google.gwt.http.client.URL;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONBoolean;
import com.google.gwt.json.client.JSONNumber;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.json.client.JSONValue;

public class Rpc {
    private static int request_id = 0;
    private static final String RPC_URL = GWT.getHostPageBaseURL()+"../rpc/";
    private final RequestBuilder request = new RequestBuilder(
            RequestBuilder.POST, URL.encode(RPC_URL));
    private ArrayList<RpcHandler> handlers = new ArrayList<RpcHandler>();

    public void addRpcHandler(RpcHandler handler) {
        handlers.add(handler);
    }

    public void send(String cmd, JSONValue args, RpcCallback callback) {
        // format json commands
        ++request_id;
        JSONObject json_cmd = new JSONObject();
        json_cmd.put("method", new JSONString(cmd));
        json_cmd.put("id", new JSONNumber(request_id));
        json_cmd.put("params", args);

        callback.setRpcHandlers(handlers);
        for (RpcHandler h : handlers)
            h.onRpcStart();
        try {
            request.sendRequest(json_cmd.toString(), callback);
        }
        catch (RequestException ex) {
            callback.onRequestError();
        }
    }

    public void getStatus(RpcCallback callback) {
        send("status", new JSONArray(), callback);
    }

    public void getStats(RpcCallback callback) {
        send("stats", new JSONArray(), callback);
    }

    public void getModeList(RpcCallback callback) {
        send("availablemodes", new JSONArray(), callback);
    }

    public void setMode(String mode, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(mode));
        send("setmode", args, callback);
    }

    public void setRating(int[] mediaIds, int rating, RpcCallback callback) {
        JSONArray args = new JSONArray();
        JSONArray jsonMediaIds = new JSONArray();
        int idx = 0;
        for (int id : mediaIds) {
            jsonMediaIds.set(idx, new JSONNumber(id));
            idx ++;
        }
        args.set(0, jsonMediaIds);
        args.set(1, new JSONNumber(rating));
        send("setRating", args, callback);
    }

    public void setOption(String source, String oName,
            String oValue, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(source));
        args.set(1, new JSONString(oName));
        args.set(2, new JSONString(oValue));
        send("setOption", args, callback);
    }

    public void setOption(String source, String oName,
            boolean oValue, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(source));
        args.set(1, new JSONString(oName));
        args.set(2, JSONBoolean.getInstance(oValue));
        send("setOption", args, callback);
    }

    /*
     * Player commmands
     */

    public void playToggle(RpcCallback callback) {
        send("player.playToggle", new JSONArray(), callback);
    }

    public void stop(RpcCallback callback) {
        send("player.stop", new JSONArray(), callback);
    }

    public void next(RpcCallback callback) {
        send("player.next", new JSONArray(), callback);
    }

    public void previous(RpcCallback callback) {
        send("player.previous", new JSONArray(), callback);
    }

    public void setVolume(int volume, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONNumber(volume));
        send("player.setVolume", args, callback);
    }

    public void getCurrent(RpcCallback callback) {
        send("player.current", new JSONArray(), callback);
    }

    public void seek(int pos, RpcCallback callback) {
        seek(pos, false, callback);
    }

    public void seek(int pos, boolean relative, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONNumber(pos));
        args.set(1, JSONBoolean.getInstance(relative));
        send("player.seek", args, callback);
    }

    public void setPlayerOption(String optionName, String optionValue,
            RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(optionName));
        args.set(1, new JSONString(optionValue));
        send("player.setPlayerOption", args, callback);
    }

    public void goTo(int id, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONNumber(id));
        send("player.goto", args, callback);
    }

    public void goTo(int id, String source, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONNumber(id));
        args.set(1, new JSONString("id"));
        args.set(2, new JSONString(source));
        send("player.goto", args, callback);
    }

    public void getCover(int mediaId, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONNumber(mediaId));
        send("web.writecover", args, callback);
    }

    /*
     * library commands
     */
    public void libGetDirectory(String library, String dir,
            RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(dir));
        send(library+"lib.getDir", args, callback);
    }

    public void libUpdate(String library, RpcCallback callback) {
        send(library+"lib.update", new JSONArray(), callback);
    }

    public void libSearch(String library, String pattern,
            String type, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(pattern));
        args.set(1, new JSONString(type));
        send(library+"lib.search", args, callback);
    }

    /*
     * Recorded playlist commands
     */
    public void recPlsList(RpcCallback callback) {
        send("recpls.list", new JSONArray(), callback);
    }

    public void recPlsErase(JSONArray ids, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, ids);
        send("recpls.erase", args, callback);
    }

    public void recPlsCreate(String name, String type, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(name));
        args.set(1, new JSONString(type));
        send("recpls.create", args, callback);
    }

    public void recPlsGet(String plsId, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(plsId));
        send("recpls.get", args, callback);
    }

    public void recPlsMagicGetProperties(String plsId, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(plsId));
        send("recpls.magicGetProperties", args, callback);
    }

    public void recPlsMagicSetProperty(String plsId, String key, String value,
            RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(plsId));
        args.set(1, new JSONString(key));
        args.set(2, new JSONString(value));
        send("recpls.magicSetProperty", args, callback);
    }

    public void recPlsMagicAddFilter(String plsId, MediaFilter filter,
            RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(plsId));
        args.set(1, filter.toJSON());
        send("recpls.magicAddFilter", args, callback);
    }

    public void recPlsMagicClearFilter(String plsId, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(plsId));
        send("recpls.magicClearFilter", args, callback);
    }

    /*
     * Playlist commands
     */

    public void plsModeShuffle(RpcCallback callback) {
        send("playlist.shuffle", new JSONArray(), callback);
    }

    public void plsModeClear(RpcCallback callback) {
        send("playlist.clear", new JSONArray(), callback);
    }

    public void plsModeRemove(String[] ids, RpcCallback callback) {
        JSONArray args = new JSONArray();
        JSONArray jsonIds = new JSONArray();
        int idx = 0;
        for (String id : ids) {
            jsonIds.set(idx, new JSONString(id));
            idx ++;
        }
        args.set(0, jsonIds);
        send("playlist.remove", args, callback);
    }

    public void plsModeLoadPath(JSONArray sel, int pos, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, sel);
        if (pos != -1)
            args.set(1, new JSONNumber(pos));
        send("playlist.addPath", args, callback);
    }

    public void plsModeLoadIds(JSONArray sel, int pos, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, sel);
        if (pos != -1)
            args.set(1, new JSONNumber(pos));
        send("playlist.addIds", args, callback);
    }

    public void plsModeLoadPls(JSONArray sel, int pos, RpcCallback callback) {
        JSONArray args = new JSONArray();
         args.set(0, sel);
         if (pos != -1)
             args.set(1, new JSONNumber(pos));
         send("playlist.loads", args, callback);
    }

    public void plsModeSave(String plsName, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(plsName));
        send("playlist.save", args, callback);
    }

    /*
     * Webradio commands
     */

    public void wbModeGetSources(RpcCallback callback) {
        send("webradio.getAvailableSources", new JSONArray(), callback);
    }

    public void wbModeGetSourceCategories(String source, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(source));
        send("webradio.getSourceCategories", args, callback);
    }

    public void wbModeSetSource(String source, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(source));
        send("webradio.setSource", args, callback);
    }

    public void wbModeSetSourceCategorie(String cat, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(cat));
        send("webradio.setSourceCategorie", args, callback);
    }

    public void wbModeRemove(String[] ids, RpcCallback callback) {
        JSONArray args = new JSONArray();
        JSONArray jsonIds = new JSONArray();
        int idx = 0;
        for (String id : ids) {
            jsonIds.set(idx, new JSONString(id));
            idx ++;
        }
        args.set(0, jsonIds);
        send("webradio.localRemove", args, callback);
    }

    public void wbModeClear(RpcCallback callback) {
        send("webradio.localClear", new JSONArray(), callback);
    }

    public void wbModeAdd(String name, String url, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(name));
        JSONArray urls = new JSONArray();
        urls.set(0, new JSONString(url));
        args.set(1, urls);
        send("webradio.localAdd", args, callback);
    }

    /*
     * Queue commands
     */

    public void queueClear(RpcCallback callback) {
        send("queue.clear", new JSONArray(), callback);
    }

    public void queueRemove(String[] ids, RpcCallback callback) {
        JSONArray args = new JSONArray();
        JSONArray jsonIds = new JSONArray();
        int idx = 0;
        for (String id : ids) {
            jsonIds.set(idx, new JSONString(id));
            idx ++;
        }
        args.set(0, jsonIds);
        send("queue.remove", args, callback);
    }

    public void queueLoadPath(JSONArray sel, int pos, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, sel);
        if (pos != -1)
            args.set(1, new JSONNumber(pos));
        send("queue.addPath", args, callback);
    }

    public void queueLoadIds(JSONArray sel, int pos, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, sel);
        if (pos != -1)
            args.set(1, new JSONNumber(pos));
        send("queue.addIds", args, callback);
    }

    public void queueModeLoadPls(JSONArray sel, int pos, RpcCallback callback) {
        JSONArray args = new JSONArray();
         args.set(0, sel);
         if (pos != -1)
             args.set(1, new JSONNumber(pos));
         send("queue.loads", args, callback);
    }

    /*
     * Panel commands
     */

    public void panelModeActiveList(RpcCallback callback) {
        send("panel.activeList", new JSONArray(), callback);
    }

    public void panelModeGetTags(RpcCallback callback) {
        send("panel.tags", new JSONArray(), callback);
    }

    public void panelModeSetActiveList(String mode, String pls,
            RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(mode));
        args.set(1, new JSONString(pls));
        send("panel.setActiveList", args, callback);
    }

    public void panelModeClearAll(RpcCallback callback) {
        send("panel.clearAll", new JSONArray(), callback);
    }

    public void panelModeSetSearch(String tag, String value,
            RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(tag));
        args.set(1, new JSONString(value));
        send("panel.setSearch", args, callback);
    }

    public void panelModeClearSearch(RpcCallback callback) {
        send("panel.clearSearch", new JSONArray(), callback);
    }

    public void panelModeSetFilter(String tag, String[] values,
            RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(tag));
        JSONArray jsonIds = new JSONArray();
        int idx = 0;
        for (String value : values) {
            jsonIds.set(idx, new JSONString(value));
            idx ++;
        }
        args.set(1, jsonIds);
        send("panel.setFilter", args, callback);
    }

    public void panelModeRemoveFilter(String tag, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(tag));
        send("panel.removeFilter", args, callback);
    }

    public void panelModeBuildPanel(String updatedTag, RpcCallback callback) {
        JSONArray args = new JSONArray();
        if (updatedTag != null) {
            args.set(0, new JSONString(updatedTag));
        }
        send("web.buildPanel", args, callback);
    }

    /*
     * Video Commands
     */

    public void videoModeSet(String value, String type, RpcCallback callback) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(value));
        args.set(1, new JSONString(type));
        send("video.set", args, callback);
    }
}

//vim: ts=4 sw=4 expandtab