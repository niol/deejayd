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

import org.mroy31.deejayd.common.widgets.LibraryManager;
import org.mroy31.deejayd.webui.cellview.AudioLibView;
import org.mroy31.deejayd.webui.cellview.AudioSearchView;
import org.mroy31.deejayd.webui.cellview.PlsListView;
import org.mroy31.deejayd.webui.resources.WebuiResources;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.logical.shared.SelectionEvent;
import com.google.gwt.event.logical.shared.SelectionHandler;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.TabLayoutPanel;
import com.google.gwt.user.client.ui.Widget;

public class PlaylistPanel extends WebuiPanel {

    private static PlaylistPanelUiBinder uiBinder = GWT
            .create(PlaylistPanelUiBinder.class);
    interface PlaylistPanelUiBinder extends UiBinder<Widget, PlaylistPanel> {}

    @UiField(provided = true) final LibraryManager updateButton;
    @UiField TabLayoutPanel tabPanel;

    @UiField Label dirHeader;
    @UiField(provided = true) AudioLibView audioLibView;
    @UiField Label searchHeader;
    @UiField(provided = true) AudioSearchView audioSearchView;
    @UiField Label plsHeader;
    @UiField(provided = true)  PlsListView plsListView;
    @UiField(provided = true) final WebuiResources resources;

    private WebuiLayout ui;

    public PlaylistPanel(WebuiLayout webui) {
        super("playlist");

        this.resources = webui.resources;
        this.updateButton = webui.audioLibrary;
        this.ui = webui;
        this.audioLibView = new AudioLibView(webui);
        this.audioSearchView = new AudioSearchView(webui);
        this.plsListView = new PlsListView(webui);

        initWidget(uiBinder.createAndBindUi(this));
        // set header label
        dirHeader.setText(ui.i18nConstants.directory());
        searchHeader.setText(ui.i18nConstants.search());
        plsHeader.setText(ui.i18nConstants.playlists());

        tabPanel.addSelectionHandler(new SelectionHandler<Integer>() {
            public void onSelection(SelectionEvent<Integer> event) {
                if (event.getSelectedItem().equals(1))
                    audioSearchView.focus();
            }
        });

    }

}

//vim: ts=4 sw=4 expandtab