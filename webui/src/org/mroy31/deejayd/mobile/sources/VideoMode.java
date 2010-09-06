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
import org.mroy31.deejayd.mobile.client.SourcePanel;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.HorizontalPanel;


public class VideoMode extends DefaultMode {
    private OptionPanel optionPanel = new OptionPanel("video", hideCtxCmd);

    public VideoMode(SourcePanel manager) {
        super("video", manager);
    }

    @Override
    public String getTitle() {
        return ui.i18nConst.videoMode();
    }

    @Override
    public void initToolbar(HorizontalPanel toolbar) {
        Button option = new Button();
        option.addStyleName(ui.resources.mobileCss().playerButton());
        option.addStyleName(ui.resources.mobileCss().option());
        option.addClickHandler(new ClickHandler() {
            public void onClick(ClickEvent event) {
                manager.setContextWidget(ui.i18nConst.options(), optionPanel);
                manager.setContextVisible(true);
            }
        });
        toolbar.add(option);

        Button loadFiles = new Button();
        loadFiles.addStyleName(ui.resources.mobileCss().playerButton());
        loadFiles.addStyleName(ui.resources.mobileCss().add());
        loadFiles.addClickHandler(new ClickHandler() {
            public void onClick(ClickEvent event) {
                manager.setContextWidget(ui.i18nConst.addFiles(),
                        new VideoLibrary(hideCtxCmd));
                manager.setContextVisible(true);
            }
        });
        toolbar.add(loadFiles);
    }

    @Override
    public void onStatusChange(StatusChangeEvent event) {
        super.onStatusChange(event);
        optionPanel.update(event.getStatus());
    }
}

//vim: ts=4 sw=4 expandtab