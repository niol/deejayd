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

import com.google.gwt.http.client.Request;
import com.google.gwt.http.client.Response;
import com.google.gwt.json.client.JSONException;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;


public abstract class AbstractRpcCallback implements RpcCallback {
    private ArrayList<RpcHandler> handlers;

    public void onResponseReceived(Request request, Response response) {
        for (RpcHandler h : handlers)
            h.onRpcStop();

        if (200 == response.getStatusCode()) {
            // parse JSON answer
            try {
                JSONObject answer = JSONParser.parseStrict(response.getText())
                  .isObject();

                if (answer != null) {
                    if (answer.get("error").isNull() != null) {
                        // correct answer, do specific actions
                        JSONValue data = answer.get("result");
                        this.onCorrectAnswer(data.isObject().get("answer"));
                    }
                    else {
                        JSONObject error = answer.get("error").isObject();
                        String c = error.get("code").toString();
                        String msg = error.get("message").toString();
                        this.onJSONRPCError(request, c, msg);
                    }
                }

            }
            catch (JSONException ex) {
                String err = "Unable to parse Server Answer: "+ ex.getMessage();
                this.setError(err);
            }
        } else {
            this.setError("Server return an error code");
        }
    }

    public void onError(Request request, Throwable exception) {
        this.setError("Server error response");
    }

    public void onRequestError() {
        for (RpcHandler h : handlers)
            h.onRpcStop();
        this.setError("Request Error");
    }

    public void setRpcHandlers(ArrayList<RpcHandler> handlers) {
        this.handlers = handlers;
    }

    public abstract void onCorrectAnswer(JSONValue data);

    protected void setError(String error) {
        for (RpcHandler h : handlers)
            h.onRpcError(error);
    }

    /**
     * Called when a {@link org.mroy31.deejayd.rpc.Rpc} return an
     * error.
     */
     protected void onJSONRPCError(Request request, String code, String msg) {
         this.setError("Server return an JSON error "+code+" - "+msg);
     }

}

//vim: ts=4 sw=4 expandtab