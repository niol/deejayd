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

import org.mroy31.deejayd.common.events.StatusChangeEvent;
import org.mroy31.deejayd.common.events.StatusChangeHandler;
import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.common.rpc.types.Media;
import org.mroy31.deejayd.common.rpc.types.MediaList;

import com.google.gwt.view.client.AsyncDataProvider;
import com.google.gwt.view.client.HasData;
import com.google.gwt.view.client.Range;


public class MediaListProvider implements StatusChangeHandler {
    private final DeejaydUIWidget ui;
    private final String source;

    private int sourceId = -1;
    private AsyncDataProvider<Media> dataProvider = new AsyncDataProvider<Media>() {

        @Override
        protected void onRangeChanged(HasData<Media> display) {
            updateMediasOnRange(display.getVisibleRange());
        }

    };

    public MediaListProvider(DeejaydUIWidget ui, String source) {
        this.ui = ui;
        this.source = source;
    }

    public void onStatusChange(StatusChangeEvent event) {
        int id = Integer.parseInt(event.getStatus().get(source));
        if (id != sourceId) {
            sourceId = id;
            int l = Integer.parseInt(event.getStatus().get(source+"length"));
            dataProvider.updateRowCount(l, true);

            Range[] ranges = dataProvider.getRanges();
            for (final Range range : ranges)
                updateMediasOnRange(range);
        }
    }

    public AsyncDataProvider<Media> getDataProvider() {
        return dataProvider;
    }

    private void updateMediasOnRange(final Range range) {
        ui.rpc.modeGetMedia(source, range.getStart(),
                range.getLength(), new AnswerHandler<MediaList>() {

            public void onAnswer(MediaList answer) {
                dataProvider.updateRowData(range.getStart(),
                        answer.getMediaList());
            }
        });
    }
}

//vim: ts=4 sw=4 expandtab