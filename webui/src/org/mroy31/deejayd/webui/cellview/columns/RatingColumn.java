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

import com.google.gwt.cell.client.AbstractCell;
import com.google.gwt.resources.client.ImageResource;
import com.google.gwt.user.cellview.client.Column;
import com.google.gwt.user.client.ui.AbstractImagePrototype;

public class RatingColumn extends Column<Media, Integer> {

    public RatingColumn(final ImageResource star) {
        super(new AbstractCell<Integer>() {

            @Override
            public void render(Integer value, Object key, StringBuilder sb) {
                String img = AbstractImagePrototype.create(star).getHTML();

                sb.append("<div style='display:inline-block'>");
                for (int idx=1; idx<5; idx++) {
                    sb.append("<span");
                    if (value<idx)
                        sb.append(" style='opacity:0.4'");
                    sb.append(">").append(img).append("</span>");
                }
                sb.append("</div>");
            }
        });
    }

    @Override
    public Integer getValue(Media object) {
        return object.getIntAttr("rating");
    }

}

//vim: ts=4 sw=4 expandtab