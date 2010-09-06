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
import java.util.HashMap;
import java.util.List;

import org.mroy31.deejayd.common.rpc.callbacks.AbstractRpcCallback;
import org.mroy31.deejayd.common.rpc.callbacks.AckCallback;
import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.common.rpc.callbacks.CurrentCallback;
import org.mroy31.deejayd.common.rpc.callbacks.DictCallback;
import org.mroy31.deejayd.common.rpc.callbacks.FileDirListCallback;
import org.mroy31.deejayd.common.rpc.callbacks.ListCallback;
import org.mroy31.deejayd.common.rpc.callbacks.MediaListCallback;
import org.mroy31.deejayd.common.rpc.callbacks.PlsListCallback;
import org.mroy31.deejayd.common.rpc.callbacks.RpcCallback;
import org.mroy31.deejayd.common.rpc.callbacks.RpcHandler;
import org.mroy31.deejayd.common.rpc.types.FileDirList;
import org.mroy31.deejayd.common.rpc.types.Media;
import org.mroy31.deejayd.common.rpc.types.MediaFilter;
import org.mroy31.deejayd.common.rpc.types.MediaList;
import org.mroy31.deejayd.common.rpc.types.Playlist;

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
    private final AnswerHandler<String> defaultHandler;

    public Rpc(final AnswerHandler<String> defaultHandler) {
        this.defaultHandler = defaultHandler;
    }

    public void addRpcHandler(RpcHandler handler) {
        handlers.add(handler);
    }

    public void send(String cmd) {
        send(cmd, new JSONArray(), (AnswerHandler<Boolean>) null);
    }

    public void send(String cmd, JSONValue args,
            final AnswerHandler<Boolean> handler) {
        RpcCallback cb = null;
        if (handler != null) {
            cb = new AckCallback(handler);
        }
        send(cmd, args, cb);
    }

    public void send(final String cmd, JSONValue args, RpcCallback callback) {
        if (callback == null)
            callback = new AbstractRpcCallback() {
                @Override
                public void onCorrectAnswer(JSONValue data) {
                    defaultHandler.onAnswer(cmd);
                }
            };

        // format json commands
        ++request_id;
        JSONObject json_cmd = new JSONObject();
        json_cmd.put("method", new JSONString(cmd));
        json_cmd.put("id", new JSONNumber(request_id));
        json_cmd.put("params", args);

        callback.setRpcHandlers(handlers);
        try {
            for (RpcHandler h : handlers)
                h.onRpcStart();
            request.sendRequest(json_cmd.toString(), callback);
        }
        catch (RequestException ex) {
            callback.onRequestError();
        }
    }

    public void getStatus(AnswerHandler<HashMap<String, String>> handler) {
        send("status", new JSONArray(), new DictCallback(handler));
    }

    public void getStats(AnswerHandler<HashMap<String, String>> handler) {
        send("stats", new JSONArray(), new DictCallback(handler));
    }

    public void getModeList(AnswerHandler<HashMap<String, String>> handler) {
        send("availablemodes", new JSONArray(), new DictCallback(handler));
    }

    public void setMode(String mode, AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(mode));
        send("setmode", args, handler);
    }

    public void setRating(int[] mediaIds, int rating,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        JSONArray jsonMediaIds = new JSONArray();
        int idx = 0;
        for (int id : mediaIds) {
            jsonMediaIds.set(idx, new JSONNumber(id));
            idx ++;
        }
        args.set(0, jsonMediaIds);
        args.set(1, new JSONNumber(rating));
        send("setRating", args, handler);
    }

    public void setOption(String source, String oName, String oValue,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(source));
        args.set(1, new JSONString(oName));
        args.set(2, new JSONString(oValue));
        send("setOption", args, handler);
    }

    public void setOption(String source, String oName, boolean oValue,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(source));
        args.set(1, new JSONString(oName));
        args.set(2, JSONBoolean.getInstance(oValue));
        send("setOption", args, handler);
    }

    /*
     * Player commmands
     */

    public void playToggle() {
        send("player.playToggle");
    }

    public void stop() {
        send("player.stop");
    }

    public void next() {
        send("player.next");
    }

    public void previous() {
        send("player.previous");
    }

    public void setVolume(int volume, AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONNumber(volume));
        send("player.setVolume", args, handler);
    }

    public void getCurrent(AnswerHandler<Media> handler) {
        send("player.current", new JSONArray(), new CurrentCallback(handler));
    }

    public void seek(int pos, AnswerHandler<Boolean> handler) {
        seek(pos, false, handler);
    }

    public void seek(int pos, boolean relative, AnswerHandler<Boolean> handler){
        JSONArray args = new JSONArray();
        args.set(0, new JSONNumber(pos));
        args.set(1, JSONBoolean.getInstance(relative));
        send("player.seek", args, handler);
    }

    public void setPlayerOption(String optionName, String optionValue,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(optionName));
        args.set(1, new JSONString(optionValue));
        send("player.setPlayerOption", args, handler);
    }

    public void goTo(int id, AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONNumber(id));
        send("player.goto", args, handler);
    }

    public void goTo(int id, String source, AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONNumber(id));
        args.set(1, new JSONString("id"));
        args.set(2, new JSONString(source));
        send("player.goto", args, handler);
    }

    public void goTo(String id, AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(id));
        args.set(1, new JSONString("dvd_id"));
        args.set(2, new JSONString("dvd"));
        send("player.goto", args, handler);
    }

    public void getCover(int mediaId,
            AnswerHandler<HashMap<String,String>> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONNumber(mediaId));
        send("web.writecover", args, new DictCallback(handler));
    }

    /*
     * library commands
     */
    public void libGetDirectory(String library, String dir,
            AnswerHandler<FileDirList> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(dir));
        send(library+"lib.getDir", args, new FileDirListCallback(handler));
    }

    public void libUpdate(String library,
            AnswerHandler<HashMap<String,String>> handler) {
        send(library+"lib.update", new JSONArray(), new DictCallback(handler));
    }

    public void libSearch(String library, String pattern,
            String type, AnswerHandler<FileDirList> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(pattern));
        args.set(1, new JSONString(type));
        send(library+"lib.search", args, new FileDirListCallback(handler));
    }

    public void audioLibTagList(String tag, MediaFilter filter,
            AnswerHandler<List<String>> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(tag));
        args.set(1, filter.toJSON());
        send("audiolib.taglist", args, new ListCallback(handler));
    }

    /*
     * Recorded playlist commands
     */
    public void recPlsList(AnswerHandler<List<Playlist>> handler) {
        send("recpls.list", new JSONArray(), new PlsListCallback(handler));
    }

    public void recPlsErase(JSONArray ids, AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, ids);
        send("recpls.erase", args, handler);
    }

    public void recPlsCreate(String name, String type,
            AnswerHandler<HashMap<String, String>> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(name));
        args.set(1, new JSONString(type));
        send("recpls.create", args, new DictCallback(handler));
    }

    public void recPlsGet(String plsId,AnswerHandler<MediaList> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(plsId));
        send("recpls.get", args, new MediaListCallback(handler));
    }

    public void recPlsStaticAdd(String plsId, String[] ids,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(plsId));
        JSONArray idsArray = new JSONArray();
        for (String id : ids)
            idsArray.set(idsArray.size(), new JSONString(id));
        args.set(1, idsArray);
        args.set(2, new JSONString("id"));

        send("recpls.staticAdd", args, handler);
    }

    public void recPlsMagicGetProperties(String plsId,
            AnswerHandler<HashMap<String, String>> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(plsId));
        send("recpls.magicGetProperties", args, new DictCallback(handler));
    }

    public void recPlsMagicSetProperty(String plsId, String key, String value,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(plsId));
        args.set(1, new JSONString(key));
        args.set(2, new JSONString(value));
        send("recpls.magicSetProperty", args, handler);
    }

    public void recPlsMagicAddFilter(String plsId, MediaFilter filter,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(plsId));
        args.set(1, filter.toJSON());
        send("recpls.magicAddFilter", args, handler);
    }

    public void recPlsMagicClearFilter(String plsId,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(plsId));
        send("recpls.magicClearFilter", args, handler);
    }

    /*
     * Generic source command
     */
    public void modeGetMedia(String source,
            int start, int length, AnswerHandler<MediaList> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONNumber(start));
        args.set(1, new JSONNumber(length));
        send(source+".get", args, new MediaListCallback(handler));
    }

    /*
     * Playlist commands
     */
    public void plsModeShuffle() {
        send("playlist.shuffle");
    }

    public void plsModeClear() {
        send("playlist.clear");
    }

    public void plsModeRemove(String[] ids, AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        JSONArray jsonIds = new JSONArray();
        int idx = 0;
        for (String id : ids) {
            jsonIds.set(idx, new JSONString(id));
            idx ++;
        }
        args.set(0, jsonIds);
        send("playlist.remove", args, handler);
    }

    public void plsModeMove(String[] ids, int pos,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        JSONArray jsonIds = new JSONArray();
        int idx = 0;
        for (String id : ids) {
            jsonIds.set(idx, new JSONString(id));
            idx ++;
        }
        args.set(0, jsonIds);
        args.set(1, new JSONNumber(pos));
        send("playlist.move", args, handler);
    }

    public void plsModeLoadPath(JSONArray sel, int pos,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, sel);
        if (pos != -1)
            args.set(1, new JSONNumber(pos));
        send("playlist.addPath", args, handler);
    }

    public void plsModeLoadIds(JSONArray sel, int pos,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, sel);
        if (pos != -1)
            args.set(1, new JSONNumber(pos));
        send("playlist.addIds", args, handler);
    }

    public void plsModeLoadPls(JSONArray sel, int pos,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
         args.set(0, sel);
         if (pos != -1)
             args.set(1, new JSONNumber(pos));
         send("playlist.loads", args, handler);
    }

    public void plsModeSave(String plsName, AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(plsName));
        send("playlist.save", args, handler);
    }

    /*
     * Webradio commands
     */

    public void wbModeGetSources(AnswerHandler<HashMap<String,String>> handler) {
        send("webradio.getAvailableSources", new JSONArray(),
                new DictCallback(handler));
    }

    public void wbModeGetSourceCategories(String source,
            AnswerHandler<List<String>> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(source));
        send("webradio.getSourceCategories", args, new ListCallback(handler));
    }

    public void wbModeSetSource(String source, AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(source));
        send("webradio.setSource", args, handler);
    }

    public void wbModeSetSourceCategorie(String cat,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(cat));
        send("webradio.setSourceCategorie", args, handler);
    }

    public void wbModeRemove(String[] ids, AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        JSONArray jsonIds = new JSONArray();
        int idx = 0;
        for (String id : ids) {
            jsonIds.set(idx, new JSONString(id));
            idx ++;
        }
        args.set(0, jsonIds);
        send("webradio.localRemove", args, handler);
    }

    public void wbModeClear() {
        send("webradio.localClear");
    }

    public void wbModeAdd(String name, String url,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(name));
        JSONArray urls = new JSONArray();
        urls.set(0, new JSONString(url));
        args.set(1, urls);
        send("webradio.localAdd", args, handler);
    }

    /*
     * Queue commands
     */

    public void queueClear() {
        send("queue.clear");
    }

    public void queueRemove(String[] ids, AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        JSONArray jsonIds = new JSONArray();
        int idx = 0;
        for (String id : ids) {
            jsonIds.set(idx, new JSONString(id));
            idx ++;
        }
        args.set(0, jsonIds);
        send("queue.remove", args, handler);
    }

    public void queueMove(String[] ids, int pos,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        JSONArray jsonIds = new JSONArray();
        int idx = 0;
        for (String id : ids) {
            jsonIds.set(idx, new JSONString(id));
            idx ++;
        }
        args.set(0, jsonIds);
        args.set(1, new JSONNumber(pos));
        send("queue.move", args, handler);
    }

    public void queueLoadPath(JSONArray sel, int pos,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, sel);
        if (pos != -1)
            args.set(1, new JSONNumber(pos));
        send("queue.addPath", args, handler);
    }

    public void queueLoadIds(JSONArray sel, int pos,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, sel);
        if (pos != -1)
            args.set(1, new JSONNumber(pos));
        send("queue.addIds", args, handler);
    }

    public void queueModeLoadPls(JSONArray sel, int pos,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
         args.set(0, sel);
         if (pos != -1)
             args.set(1, new JSONNumber(pos));
         send("queue.loads", args, handler);
    }

    /*
     * Panel commands
     */

    public void panelModeActiveList(
            AnswerHandler<HashMap<String,String>> handler) {
        send("panel.activeList", new JSONArray(), new DictCallback(handler));
    }

    public void panelModeGetTags(AnswerHandler<List<String>> handler) {
        send("panel.tags", new JSONArray(), new ListCallback(handler));
    }

    public void panelModeSetActiveList(String mode, String pls,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(mode));
        args.set(1, new JSONString(pls));
        send("panel.setActiveList", args, handler);
    }

    public void panelModeClearAll() {
        send("panel.clearAll");
    }

    public void panelModeSetSearch(String tag, String value,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(tag));
        args.set(1, new JSONString(value));
        send("panel.setSearch", args, handler);
    }

    public void panelModeClearSearch() {
        send("panel.clearSearch");
    }

    public void panelModeSetFilter(String tag, String[] values,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(tag));
        JSONArray jsonIds = new JSONArray();
        int idx = 0;
        for (String value : values) {
            jsonIds.set(idx, new JSONString(value));
            idx ++;
        }
        args.set(1, jsonIds);
        send("panel.setFilter", args, handler);
    }

    public void panelModeRemoveFilter(String tag,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(tag));
        send("panel.removeFilter", args, handler);
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

    public void videoModeSet(String value, String type,
            AnswerHandler<Boolean> handler) {
        JSONArray args = new JSONArray();
        args.set(0, new JSONString(value));
        args.set(1, new JSONString(type));
        send("video.set", args, handler);
    }

    /*
     * Dvd Commands
     */

    public void dvdModeReload() {
        send("dvd.reload");
    }

    public void dvdGetInfo(RpcCallback callback) {
        send("dvd.get", new JSONArray(), callback);
    }
}

//vim: ts=4 sw=4 expandtab