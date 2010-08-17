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

package org.mroy31.deejayd.common.events;

import java.util.HashMap;

import com.google.gwt.event.shared.GwtEvent;
import com.google.gwt.event.shared.HasHandlers;

public class StatsChangeEvent extends GwtEvent<StatsChangeHandler>{
    private HashMap<String, String> stats;
    public static final Type<StatsChangeHandler> TYPE = new Type<StatsChangeHandler>();


    public StatsChangeEvent(HashMap<String, String> stats) {
        super();
        this.stats = stats;
    }

    public HashMap<String, String> getStats() {
        return stats;
    }

    @Override
    protected void dispatch(StatsChangeHandler handler) {
        handler.onStatsChange(this);
    }

    @Override
    public final Type<StatsChangeHandler> getAssociatedType() {
        return TYPE;
    }

    public static Type<StatsChangeHandler> getType() {
        return TYPE;
    }

    public static <S extends HasStatsChangeHandlers & HasHandlers>
        void fire(S source, HashMap<String, String> stats) {
        StatsChangeEvent event = new StatsChangeEvent(stats);
        source.fireEvent(event);
    }
}

//vim: ts=4 sw=4 expandtab