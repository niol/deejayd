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

import org.mroy31.deejayd.common.events.HasPlsListChangeHandlers;
import org.mroy31.deejayd.common.events.HasStatsChangeHandlers;
import org.mroy31.deejayd.common.events.HasStatusChangeHandlers;
import org.mroy31.deejayd.common.events.PlsListChangeEvent;
import org.mroy31.deejayd.common.events.PlsListChangeHandler;
import org.mroy31.deejayd.common.events.StatsChangeEvent;
import org.mroy31.deejayd.common.events.StatsChangeHandler;
import org.mroy31.deejayd.common.events.StatusChangeEvent;
import org.mroy31.deejayd.common.events.StatusChangeHandler;
import org.mroy31.deejayd.common.i18n.CommonI18nConstants;
import org.mroy31.deejayd.common.i18n.CommonI18nMessages;
import org.mroy31.deejayd.common.rpc.Rpc;
import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;

import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.Widget;

public abstract class DeejaydUIWidget extends Composite
        implements HasStatusChangeHandlers, HasStatsChangeHandlers,
                   HasPlsListChangeHandlers {
    public final Rpc rpc = new Rpc(new AnswerHandler<String>() {
        public void onAnswer(String cmd) {
            update();
        }
    });

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

    public HandlerRegistration addStatusChangeHandler(
            StatusChangeHandler handler) {
        return addHandler(handler, StatusChangeEvent.getType());
    }

    public HandlerRegistration addStatsChangeHandler(
            StatsChangeHandler handler) {
        return addHandler(handler, StatsChangeEvent.getType());
    }

    public HandlerRegistration addPlsListChangeHandler(
            PlsListChangeHandler handler) {
        return addHandler(handler, PlsListChangeEvent.getType());
    }

    public void setMessage(String message) {
        setMessage(message, "information");
    }

    public void update() {
        this.rpc.getStatus(new AnswerHandler<HashMap<String,String>>() {
            public void onAnswer(HashMap<String, String> status) {
                fireEvent(new StatusChangeEvent(status));
            }
        });
    }

    public void updatePlsList() {
        fireEvent(new PlsListChangeEvent());
    }

    abstract public void setMessage(String message, String type);
    
    abstract public CommonI18nConstants getI18nConstants();
    abstract public CommonI18nMessages getI18nMessages();

}

//vim: ts=4 sw=4 expandtab