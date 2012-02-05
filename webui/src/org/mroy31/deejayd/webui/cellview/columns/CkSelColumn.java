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
import com.google.gwt.dom.client.InputElement;
import com.google.gwt.dom.client.TableRowElement;
import com.google.gwt.user.cellview.client.Column;
import com.google.gwt.user.cellview.client.DeejaydCellTable;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.view.client.SelectionChangeEvent;

public class CkSelColumn<T> extends Column<T, Boolean> {
    private final DeejaydCellTable<T> list;
    private final CheckBox allCheckbox;

    public CkSelColumn(DeejaydCellTable<T> l) {
    	this(l, null);
    }
    
    public CkSelColumn(DeejaydCellTable<T> l, CheckBox allCk) {
        super(new CkSelCell());

        this.allCheckbox = allCk;
        this.list = l;
        setFieldUpdater(new FieldUpdater<T, Boolean>() {

            public void update(int index, T object, Boolean value) {
                // Called when the user clicks on a checkbox.
                list.getSelectionModel().setSelected(object, value);
                if (allCheckbox != null) { // clear header checkbox if available
                	allCheckbox.setValue(false);
                }
            }
        });

        // update checkbox based on selection state
        list.getSelectionModel().addSelectionChangeHandler(new SelectionChangeEvent.Handler() {

            public void onSelectionChange(SelectionChangeEvent event) {

                int idx = 0;
                for (T m : list.getVisibleItems()) {
                    TableRowElement elt = list.getRowElement(idx);
                    InputElement input = elt.getFirstChild().getFirstChild().getFirstChild().cast();
                    if (list.getSelectionModel().isSelected(m) != input.isChecked())
                        input.setChecked(list.getSelectionModel().isSelected(m));
                    idx ++;
                }
            }
         });
    }

    @Override
    public Boolean getValue(T object) {
        return list.getSelectionModel().isSelected(object);
    }

}

//vim: ts=4 sw=4 expandtab