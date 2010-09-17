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

import com.google.gwt.cell.client.FieldUpdater;
import com.google.gwt.dom.client.Element;
import com.google.gwt.dom.client.InputElement;
import com.google.gwt.resources.client.ImageResource;
import com.google.gwt.user.cellview.client.Column;
import com.google.gwt.user.cellview.client.DeejaydCellTable;

public class GrippyColumn<T> extends Column<T, String> {
    private final String source;
    private final DeejaydCellTable<T> view;

    public GrippyColumn(String source, DeejaydCellTable<T> v, ImageResource grippy) {
        super(new GrippyCell<T>(v, grippy));
        this.source = source;
        this.view = v;

        setFieldUpdater(new FieldUpdater<T, String>() {

            public void update(int index, T object, String value) {
                Boolean v = value.equals("true");
                view.getSelectionModel().setSelected(object, v);
                // select input checkbox
                Element cell = Element.as(view.getRowElement(index).getChild(1));
                InputElement input = cell.getFirstChildElement()
                    .getFirstChildElement().cast();
                input.setChecked(v);
            }
        });
    }

    @Override
    public String getValue(T object) {
        return source+"-"+(String) view.getKeyProvider().getKey(object);
    }

}

//vim: ts=4 sw=4 expandtab