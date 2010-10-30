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

import org.mroy31.deejayd.common.rpc.types.MediaListSort;
import org.mroy31.deejayd.webui.cellview.columns.MediaAttrColumn;
import org.mroy31.deejayd.webui.cellview.columns.RatingColumn;
import org.mroy31.deejayd.webui.client.WebuiLayout;
import org.mroy31.deejayd.webui.i18n.WebuiConstants;

import com.google.gwt.user.client.ui.Label;

public class SortVideoList extends SortMediaList {

    public SortVideoList(WebuiLayout ui) {
        super(ui, "video", DEFAULT_PAGE_SIZE);
        WebuiConstants i18n = ui.i18nConstants;

        sortCols.put("title", new HeaderCol(ui, i18n.title(), "title"));
        addColumn(new MediaAttrColumn("title", ui), sortCols.get("title"), 2);

        addColumn(new MediaAttrColumn("videowidth", ui),
                new Label(i18n.width()), "40px");
        addColumn(new MediaAttrColumn("videoheight", ui),
                new Label(i18n.height()), "40px");
        addColumn(new MediaAttrColumn("external_subtitle", ui),
                new Label(i18n.subtitle()), "65px");
        addColumn(new MediaAttrColumn("length", ui),
                new Label(i18n.length()), "50px");

        sortCols.put("rating", new HeaderCol(ui, i18n.rating(), "rating"));
        addColumn(new RatingColumn(ui.resources.star()),
                sortCols.get("rating"), "70px");
    }

    @Override
    void updateSort(String tag, String value) {
        MediaListSort sort = new MediaListSort();
        if (!"unsorted".equals(value))
            sort.add(new MediaListSort.TagSort(tag, value));

        ui.rpc.videoModeSetSort(sort, null);
    }

}

//vim: ts=4 sw=4 expandtab