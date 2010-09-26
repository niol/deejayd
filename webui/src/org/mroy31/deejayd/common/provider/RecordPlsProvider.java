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

package org.mroy31.deejayd.common.provider;

import java.util.List;

import org.mroy31.deejayd.common.events.PlsListChangeEvent;
import org.mroy31.deejayd.common.events.PlsListChangeHandler;
import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.common.rpc.types.Playlist;
import org.mroy31.deejayd.common.widgets.DeejaydUIWidget;

import com.google.gwt.view.client.AsyncDataProvider;
import com.google.gwt.view.client.HasData;

public class RecordPlsProvider implements PlsListChangeHandler {
    private final DeejaydUIWidget ui;
    private AsyncDataProvider<Playlist> dataProvider = new AsyncDataProvider<Playlist>() {

        @Override
        protected void onRangeChanged(HasData<Playlist> display) {
        }

    };

    public RecordPlsProvider(DeejaydUIWidget ui) {
        this.ui = ui;
        ui.addPlsListChangeHandler(this);
    }

    public AsyncDataProvider<Playlist> getDataProvider() {
        return dataProvider;
    }

    public void onPlsListChange(PlsListChangeEvent event) {
        ui.rpc.recPlsList(new AnswerHandler<List<Playlist>>() {

            public void onAnswer(List<Playlist> answer) {
                dataProvider.updateRowCount(answer.size(), true);
                dataProvider.updateRowData(0, answer);
            }
        });
    }

}

//vim: ts=4 sw=4 expandtab