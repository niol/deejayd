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

import java.util.ArrayList;

import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.common.rpc.types.Media;
import org.mroy31.deejayd.common.rpc.types.MediaList;
import org.mroy31.deejayd.common.widgets.DeejaydUIWidget;

import com.google.gwt.view.client.AsyncDataProvider;
import com.google.gwt.view.client.HasData;
import com.google.gwt.view.client.Range;

public class LibrarySearchProvider {
    private final DeejaydUIWidget ui;
    private final String libType;
    private ArrayList<Media> currentList = new ArrayList<Media>();
    private AsyncDataProvider<Media> dataProvider=new AsyncDataProvider<Media>() {

        @Override
        protected void onRangeChanged(HasData<Media> display) {
            Range rg = display.getVisibleRange();
            if (currentList.size() > rg.getStart()) {
                int toIdx = Math.min(currentList.size()-1,
                        rg.getStart()+rg.getLength());
                dataProvider.updateRowData(rg.getStart(),
                        currentList.subList(rg.getStart(), toIdx));
            } else {
                dataProvider.updateRowData(rg.getStart(),
                        new ArrayList<Media>());
            }
        }

    };

    public LibrarySearchProvider(DeejaydUIWidget ui, String libType) {
        this.ui = ui;
        this.libType = libType;
    }

    public AsyncDataProvider<Media> getDataProvider() {
        return dataProvider;
    }

    public void search(String pattern, String type) {
        ui.rpc.libSearch(libType, pattern, type, new AnswerHandler<MediaList>() {

            public void onAnswer(MediaList answer) {
                currentList = new ArrayList<Media>(answer.getMediaList());

                dataProvider.updateRowCount(answer.getMediaList().size(), true);
                dataProvider.updateRowData(0, currentList);
            }
        });
    }

    public void clear() {
        currentList.clear();

        dataProvider.updateRowCount(0, true);
        dataProvider.updateRowData(0, currentList);
    }
}

//vim: ts=4 sw=4 expandtab