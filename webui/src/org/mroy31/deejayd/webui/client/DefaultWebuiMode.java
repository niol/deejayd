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

package org.mroy31.deejayd.webui.client;

import org.mroy31.deejayd.webui.cellview.AbstractMediaList;
import org.mroy31.deejayd.webui.cellview.Pager;
import org.mroy31.deejayd.webui.resources.WebuiResources;

import com.google.gwt.core.client.GWT;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiFactory;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Widget;

public abstract class DefaultWebuiMode extends AbstractWebuiMode {

    private static WebuiModeUiBinder uiBinder = GWT
            .create(WebuiModeUiBinder.class);
    interface WebuiModeUiBinder extends UiBinder<Widget, DefaultWebuiMode> {}

    @UiField AbstractMediaList mediaList;
    @UiField HorizontalPanel bottomToolbar;
    @UiField HorizontalPanel leftBottomToolbar;
    @UiField HorizontalPanel rightBottomToolbar;
    @UiField HorizontalPanel topToolbar;
    @UiField(provided = true) final Pager pager;
    @UiField(provided = true) final WebuiResources resources;


    public DefaultWebuiMode(String source, WebuiLayout webui,
            boolean hasPlayorder, boolean hasRepeat) {
        super(source, webui, hasPlayorder, hasRepeat);
        this.resources = webui.resources;
        this.pager = new Pager(webui);
        initWidget(uiBinder.createAndBindUi(this));

        mediaList.setPager(pager);
        bottomToolbar.setCellHorizontalAlignment(rightBottomToolbar,
                HorizontalPanel.ALIGN_RIGHT);
        buildTopToolbar(topToolbar);
        buildBottomToolbar(leftBottomToolbar);
    }

    @UiFactory AbstractMediaList makeMediaList() {
        return null;
    }

    @UiFactory HorizontalPanel makeHPanel() {
        HorizontalPanel panel = new HorizontalPanel();
        panel.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);

        return panel;
    }

    @Override
    public AbstractMediaList getMediaList() {
        return mediaList;
    }

    /*
     * Abstract methods
     */
    abstract void buildTopToolbar(HorizontalPanel toolbar);
    abstract void buildBottomToolbar(HorizontalPanel toolbar);
}

//vim: ts=4 sw=4 expandtab