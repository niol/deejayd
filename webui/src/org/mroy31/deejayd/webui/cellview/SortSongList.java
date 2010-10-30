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

import org.mroy31.deejayd.common.rpc.types.Media;
import org.mroy31.deejayd.common.rpc.types.MediaListSort;
import org.mroy31.deejayd.webui.cellview.columns.GrippyCell;
import org.mroy31.deejayd.webui.cellview.columns.GrippyColumn;
import org.mroy31.deejayd.webui.cellview.columns.MediaAttrColumn;
import org.mroy31.deejayd.webui.cellview.columns.RatingColumn;
import org.mroy31.deejayd.webui.client.WebuiLayout;

import com.google.gwt.user.client.ui.Label;

public class SortSongList extends SortMediaList {

    public SortSongList(final WebuiLayout ui, String source, int pageSize) {
        super(ui, source, pageSize);

        addColumn(new GrippyColumn<Media>(source, mediaList,
                ui.resources.webuiCss().grippyCell(),
                new GrippyCell.DragStartMessage() {

                    public String onDragStart(int count) {
                        return ui.i18nMessages.songsDesc(count);
                    }
        }), new Label(""), "24px");

        addColumn(new MediaAttrColumn("tracknumber", ui), new Label("#"), "40px");

        sortCols.put("title", new HeaderCol(ui, ui.i18nConstants.title(), "title"));
        addColumn(new MediaAttrColumn("title", ui), sortCols.get("title"), 2);

        sortCols.put("artist", new HeaderCol(ui, ui.i18nConstants.artist(), "artist"));
        addColumn(new MediaAttrColumn("artist", ui), sortCols.get("artist"));

        sortCols.put("album", new HeaderCol(ui, ui.i18nConstants.album(), "album"));
        addColumn(new MediaAttrColumn("album", ui), sortCols.get("album"));

        sortCols.put("genre", new HeaderCol(ui, ui.i18nConstants.genre(), "genre"));
        addColumn(new MediaAttrColumn("genre", ui), sortCols.get("genre"));

        addColumn(new MediaAttrColumn("length", ui),
                new Label(ui.i18nConstants.length()), "50px");

        sortCols.put("rating", new HeaderCol(ui, ui.i18nConstants.rating(), "rating"));
        addColumn(new RatingColumn(ui.resources.star()),
                sortCols.get("rating"), "70px");
    }

    @Override
    void updateSort(String tag, String value) {
        MediaListSort sort = new MediaListSort();
        if (!"unsorted".equals(value))
            sort.add(new MediaListSort.TagSort(tag, value));

        ui.rpc.panelModeSetSort(sort, null);
    }

}

//vim: ts=4 sw=4 expandtab