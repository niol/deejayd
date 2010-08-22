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

package org.mroy31.deejayd.common.widgets;

import java.util.HashMap;

import org.mroy31.deejayd.common.events.HasStatsChangeHandlers;
import org.mroy31.deejayd.common.events.HasStatusChangeHandlers;
import org.mroy31.deejayd.common.events.StatsChangeEvent;
import org.mroy31.deejayd.common.events.StatsChangeHandler;
import org.mroy31.deejayd.common.events.StatusChangeEvent;
import org.mroy31.deejayd.common.events.StatusChangeHandler;
import org.mroy31.deejayd.common.rpc.DefaultRpcCallback;
import org.mroy31.deejayd.common.rpc.Rpc;

import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.Widget;

public abstract class DeejaydUIWidget extends Composite
        implements HasStatusChangeHandlers, HasStatsChangeHandlers {
    public final Rpc rpc = new Rpc();

    protected abstract class Message extends Composite {

        public Message(String message, String type) {
            initWidget(buildWidget(message, type));

            if (!type.equals("error")) {
                Timer timer = new Timer() {
                    @Override
                    public void run() {
                        removeFromParent();
                    }
                };
                timer.schedule(5000);
            }
        }

        abstract protected Widget buildWidget(String message, String type);
    }

    @Override
    public HandlerRegistration addStatusChangeHandler(
            StatusChangeHandler handler) {
        return addHandler(handler, StatusChangeEvent.getType());
    }

    @Override
    public HandlerRegistration addStatsChangeHandler(
            StatsChangeHandler handler) {
        return addHandler(handler, StatsChangeEvent.getType());
    }

    public void setError(String error) {
        setMessage(error, "error");
    }

    public void setMessage(String message) {
        setMessage(message, "information");
    }

    public void update() {
        class StatusCallback extends DefaultRpcCallback {
            public StatusCallback(DeejaydUIWidget ui) {super(ui);}
            public void onCorrectAnswer(JSONValue data) {
                JSONObject obj = data.isObject();
                // create a java map with status
                HashMap<String, String> status = new HashMap<String, String>();
                for (String key : obj.keySet()) {
                    JSONValue value = obj.get(key);
                    if (value.isString() != null) {
                        status.put(key, value.isString().stringValue());
                    } else if (value.isNumber() != null) {
                        int number = (int) value.isNumber().doubleValue();
                        status.put(key, Integer.toString(number));
                    } else if (value.isBoolean() != null) {
                        status.put(key,
                            Boolean.toString(value.isBoolean().booleanValue()));
                    }
                }

                fireEvent(new StatusChangeEvent(status));
            }
        }
        this.rpc.getStatus(new StatusCallback(this));
    }

    abstract public void setMessage(String message, String type);

}

//vim: ts=4 sw=4 expandtab