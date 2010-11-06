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
import org.mroy31.deejayd.webui.cellview.columns.GrippyCell;
import org.mroy31.deejayd.webui.cellview.columns.GrippyColumn;
import org.mroy31.deejayd.webui.cellview.columns.MediaAttrColumn;
import org.mroy31.deejayd.webui.cellview.columns.RatingColumn;
import org.mroy31.deejayd.webui.client.WebuiLayout;

import com.google.gwt.user.client.ui.Label;

public class SongList extends AbstractMediaList {

    public SongList(WebuiLayout ui, String source, int pageSize) {
        this(ui, source, pageSize, false);
    }

    public SongList(final WebuiLayout ui, String source, int pageSize,
            boolean sort) {
        super(ui, source, pageSize, true);

        addSelectionColumn();
        addColumn(new GrippyColumn<Media>(source, mediaList,
                ui.resources.webuiCss().grippyCell(),
                new GrippyCell.DragStartMessage() {

                    public String onDragStart(int count) {
                        return ui.i18nMessages.songsDesc(count);
                    }
        }), new Label(""), "24px");

        addColumn(new MediaAttrColumn("tracknumber", ui), new Label("#"), "40px");

        addColumn(new MediaAttrColumn("title", ui),
                new Label(ui.i18nConstants.title()), 2);
        addColumn(new MediaAttrColumn("artist", ui),
                new Label(ui.i18nConstants.artist()));
        addColumn(new MediaAttrColumn("album", ui),
                new Label(ui.i18nConstants.album()));
        addColumn(new MediaAttrColumn("genre", ui),
                new Label(ui.i18nConstants.genre()));
        addColumn(new MediaAttrColumn("length", ui),
                new Label(ui.i18nConstants.length()), "50px");
        addColumn(new RatingColumn(ui.resources.star()),
                new Label(ui.i18nConstants.rating()), "70px");
    }

}

//vim: ts=4 sw=4 expandtab