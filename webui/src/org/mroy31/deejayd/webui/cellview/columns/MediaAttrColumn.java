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

package org.mroy31.deejayd.webui.cellview.columns;

import org.mroy31.deejayd.common.rpc.types.Media;
import org.mroy31.deejayd.common.widgets.DeejaydUtils;

import com.google.gwt.cell.client.TextCell;
import com.google.gwt.user.cellview.client.Column;


public class MediaAttrColumn extends Column<Media, String> {
    private final String attr;

    public MediaAttrColumn(String attr) {
        super(new TextCell());
        this.attr = attr;
    }

    @Override
    public String getValue(Media object) {
        if (attr.equals("length"))
            return DeejaydUtils.formatTime(object.getIntAttr(attr));
        return object.getStrAttr(attr);
    }
}

//vim: ts=4 sw=4 expandtab