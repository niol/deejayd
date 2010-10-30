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

package org.mroy31.deejayd.webui.cellview;

import java.util.HashMap;

import org.mroy31.deejayd.common.provider.MediaListProvider;
import org.mroy31.deejayd.common.rpc.types.MediaListSort;
import org.mroy31.deejayd.webui.cellview.columns.HeaderSortColumn;
import org.mroy31.deejayd.webui.client.WebuiLayout;

public abstract class SortMediaList extends AbstractMediaList {
    protected class HeaderCol extends HeaderSortColumn {
        private String tag;

        public HeaderCol(WebuiLayout ui, String title, String tag) {
            super(ui, title);
            this.tag = tag;
        }

        @Override
        public void onSortUpdate(String value) {
            updateSort(tag, value);
        }

    }
    protected HashMap<String, HeaderCol> sortCols = new HashMap<String, HeaderCol>();

    public SortMediaList(final WebuiLayout ui, String source, int pageSize) {
        super(ui, source, pageSize, true);

        this.provider.addSortUpdateHandler(new MediaListProvider.SortUpdateHandler() {

            public void onSortUpdate(MediaListSort sort) {
                // clear current state
                for (String key : sortCols.keySet()) {
                    sortCols.get(key).setSortState("unordered");
                }

                if (sort != null) {
                    for (MediaListSort.TagSort item : sort.getList()) {
                        for (String key : sortCols.keySet()) {
                            if (item.getTag().equals(key)) {
                                sortCols.get(key).setSortState(item.getValue());
                            }
                        }
                    }
                }
            }
        });
        addSelectionColumn();
    }

    abstract void updateSort(String tag, String value);
}

//vim: ts=4 sw=4 expandtab