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

import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import com.google.gwt.view.client.ProvidesKey;
import com.google.gwt.view.client.SelectionChangeEvent;
import com.google.gwt.view.client.SelectionModel.AbstractSelectionModel;

/**
 * A selection model for deejayd cellview.
 * It is mainly based on MultiSelectionModel
 *
 *
 * @param <T> the record data type
 */
public class DeejaydSelModel<T> extends AbstractSelectionModel<T> {

    // Ensure one value per key
    private final HashMap<Object, T> selectedSet = new HashMap<Object, T>();

    private final HashMap<T, Boolean> selectionChanges = new HashMap<T, Boolean>();

    public DeejaydSelModel(ProvidesKey<T> keyProvider) {
        super(keyProvider);
    }

    /**
     * Get the set of selected items as a copy.
     *
     * @return the set of selected items
     */
    public Set<T> getSelectedSet() {
        resolveChanges();
        return new HashSet<T>(selectedSet.values());
    }

    public boolean isSelected(T object) {
        resolveChanges();
        return selectedSet.containsKey(getKey(object));
    }

    public void setSelected(T object, boolean selected) {
        selectionChanges.put(object, selected);
        scheduleSelectionChangeEvent();
    }

    public void setSelected(List<T> list, boolean selected) {
        for (T object : list) {
            selectionChanges.put(object, selected);
        }
        scheduleSelectionChangeEvent();
    }

    public void clearSelection() {
        for (T object : selectedSet.values()) {
            selectionChanges.put(object, false);
        }
        scheduleSelectionChangeEvent();
    }

    @Override
    protected void fireSelectionChangeEvent() {
        if (isEventScheduled()) {
            setEventCancelled(true);
        }

        if (resolveChanges()) {
            SelectionChangeEvent.fire(this);
        }
    }

    private boolean resolveChanges() {
        if (selectionChanges.isEmpty()) {
            return false;
        }

        boolean changed = false;
        for (Map.Entry<T, Boolean> entry : selectionChanges.entrySet()) {
            T object = entry.getKey();
            boolean selected = entry.getValue();

            Object key = getKey(object);
            T oldValue = selectedSet.get(key);
            if (selected) {
                if (oldValue == null || !oldValue.equals(object)) {
                    selectedSet.put(getKey(object), object);
                    changed = true;
                }
            } else {
                if (oldValue != null) {
                    selectedSet.remove(key);
                    changed = true;
                }
            }
        }
        selectionChanges.clear();
        return changed;
    }
}

//vim: ts=4 sw=4 expandtab