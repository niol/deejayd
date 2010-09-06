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

import java.util.HashMap;

import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONValue;

public class DictCallback extends AbstractRpcCallback {
    private final AnswerHandler<HashMap<String, String>> handler;

    public DictCallback(AnswerHandler<HashMap<String, String>> handler) {
        this.handler = handler;
    }

    @Override
    public void onCorrectAnswer(JSONValue data) {
        HashMap<String, String> answer = new HashMap<String, String>();

        JSONObject obj = data.isObject();
        for (String key : obj.keySet()) {
            JSONValue value = obj.get(key);
            if (value.isString() != null) {
                answer.put(key, value.isString().stringValue());
            } else if (value.isNumber() != null) {
                int number = (int) value.isNumber().doubleValue();
                answer.put(key, Integer.toString(number));
            } else if (value.isBoolean() != null) {
                answer.put(key,
                    Boolean.toString(value.isBoolean().booleanValue()));
            }
        }

        handler.onAnswer(answer);
    }

}

//vim: ts=4 sw=4 expandtab