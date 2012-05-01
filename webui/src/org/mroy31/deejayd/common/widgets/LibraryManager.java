/*
 * Deejayd, a media player daemon
 * Copyright (C) 2007-2012 Mickael Royer <mickael.royer@gmail.com>
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

import org.mroy31.deejayd.common.events.HasLibraryChangeHandlers;
import org.mroy31.deejayd.common.events.LibraryChangeEvent;
import org.mroy31.deejayd.common.events.LibraryChangeHandler;
import org.mroy31.deejayd.common.events.StatsChangeEvent;
import org.mroy31.deejayd.common.events.StatsChangeHandler;
import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Composite;

public class LibraryManager extends Composite implements StatsChangeHandler,
        HasLibraryChangeHandlers, ClickHandler {
    private DeejaydUIWidget ui;
    private String libraryType;
    private int lastUpdate = -1;
    private String updateId = "";
    private HashMap<String, String> messages;

    private Button updateButton;

    Timer updateTimer = new Timer() {
        @Override
        public void run() {
            ui.rpc.getStatus(new AnswerHandler<HashMap<String,String>>() {

                public void onAnswer(HashMap<String, String> answer) {
                    if (!answer.containsKey(libraryType+"_updating_db")) {
                        // library update is finished
                        stopUpdate();
                        fireEvent(new LibraryChangeEvent(libraryType));
                        ui.setMessage(messages.get("confirmation"));
                    } else if (answer.containsKey(
                            libraryType+"_updating_error")) {
                        // Library update has failed, display error msg
                        stopUpdate();
                        ui.setMessage(answer.get(libraryType+"_updating_error"),
                                "error");
                    } else {
                        String id = answer.get(libraryType+"_updating_db");
                        if (!updateId.equals(id)) {
                            // a new update has begun
                            updateId = id;
                        }
                    }

                }

                private void stopUpdate() {
                    cancel();
                    updateButton.setText(messages.get("button"));
                    updateButton.setEnabled(true);
                }
            });
        }
    };


    public LibraryManager(DeejaydUIWidget webui, String type,
            HashMap<String, String> msgs) {
        ui = webui;
        libraryType = type;
        messages = msgs;

        updateButton = new Button(messages.get("button"));
        initWidget(updateButton);
        updateButton.addClickHandler(this);
    }

    public void onStatsChange(StatsChangeEvent event) {
        HashMap<String, String> stats = event.getStats();
        int id = Integer.parseInt(stats.get("_library_update"));
        if (lastUpdate != -1 && lastUpdate != id && !updateId.equals("")) {
            fireEvent(new LibraryChangeEvent(libraryType));
        }
        lastUpdate = id;
        updateId = "";
    }

    public HandlerRegistration addLibraryChangeHandler(
            LibraryChangeHandler handler) {
        return addHandler(handler, LibraryChangeEvent.getType());
    }

    public void onClick(ClickEvent event) {
        ui.rpc.libUpdate(libraryType, new AnswerHandler<HashMap<String,String>>() {

            public void onAnswer(HashMap<String, String> answer) {
                updateId = answer.get(libraryType+"_updating_db");

                updateButton.setText(messages.get("loading"));
                updateButton.setEnabled(false);
                updateTimer.scheduleRepeating(800);
            }
        });
    }
}

//vim: ts=4 sw=4 expandtab