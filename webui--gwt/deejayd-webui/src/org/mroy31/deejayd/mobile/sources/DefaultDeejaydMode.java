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

package org.mroy31.deejayd.mobile.sources;

import org.mroy31.deejayd.common.events.StatusChangeEvent;
import org.mroy31.deejayd.mobile.client.MobileLayout;
import org.mroy31.deejayd.mobile.client.SourcePanel;

import com.google.gwt.user.client.Command;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.HorizontalPanel;

public abstract class DefaultDeejaydMode extends DeejaydMode  {
    protected final MobileLayout ui = MobileLayout.getInstance();
    protected SourcePanel manager;
    protected String name;
    protected int sourceId = -1;

    protected MediaList mediaList;
    protected HorizontalPanel toolbar = new HorizontalPanel();
    protected Command hideCtxCmd = new Command() {
        @Override
        public void execute() {
            manager.setContextVisible(false);
        }
    };

    public DefaultDeejaydMode(String name, SourcePanel manager) {
        this.manager = manager;
        this.name = name;
        this.mediaList = initMediaList();
        toolbar.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);
        toolbar.setSpacing(5);
        initToolbar(toolbar);

        FlowPanel panel = new FlowPanel();
        panel.add(toolbar);
        panel.add(mediaList);
        initWidget(panel);

        ui.addStatusChangeHandler(this);
    }

    @Override
    public void onStatusChange(StatusChangeEvent event) {
        int id = Integer.parseInt(event.getStatus().get(name));
        if (id != sourceId) {
            mediaList.updateList(
                    Integer.parseInt(event.getStatus().get(name+"length")));
            sourceId = id;
        }
    }

    abstract public void initToolbar(HorizontalPanel toolbar);
    abstract public MediaList initMediaList();

}

//vim: ts=4 sw=4 expandtab