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

import org.mroy31.deejayd.common.widgets.DeejaydUtils;
import org.mroy31.deejayd.webui.medialist.VideoRenderer;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.Widget;

public class VideoMode extends DefaultWebuiMode implements ClickHandler {

    private Label description;
    private Button goToCurrent;

    public VideoMode(WebuiLayout webui) {
        super("video", webui, true, true);
        mediaList.setOption(false, new VideoRenderer(ui, "video", loadLabel));
    }

    @Override
    void buildBottomToolbar(HorizontalPanel toolbar) {
        if (goToCurrent == null) {
            goToCurrent = new Button(ui.i18nConstants.goCurrentVideo());
            goToCurrent.setStyleName(
                    ui.resources.webuiCss().modeToolbarButton() + " " +
                    ui.resources.webuiCss().gotoButton());
            goToCurrent.addClickHandler(this);
        }
        toolbar.add(goToCurrent);
    }

    @Override
    void buildTopToolbar(HorizontalPanel toolbar) {
        HorizontalPanel optionPanel = new HorizontalPanel();
        optionPanel.add(makePlayorderWidget());
        optionPanel.add(makeRepeatWidget());
        toolbar.add(optionPanel);

        description = new Label();
        description.addStyleName(resources.webuiCss().toolbarDescLabel());
        toolbar.setHorizontalAlignment(HorizontalPanel.ALIGN_RIGHT);
        toolbar.add(description);
    }

    @Override
    protected void setDescription(int length, int timelength) {
        if (description != null) {
            if (length == 0) {
                description.setText(ui.i18nMessages.videosDesc(length));
            } else {
                String timeDesc = DeejaydUtils.formatTimeLong(timelength,
                        ui.i18nMessages);
                description.setText(ui.i18nMessages.videosDesc(length)+" ("+
                        timeDesc+")");
            }
        }
    }

    public void onClick(ClickEvent event) {
        Widget sender = (Widget) event.getSource();
        if (sender == goToCurrent) {
            if (currentPlayingPos != -1) {
                mediaList.goTo(currentPlayingPos);
            }
        }
    }

}

//vim: ts=4 sw=4 expandtab