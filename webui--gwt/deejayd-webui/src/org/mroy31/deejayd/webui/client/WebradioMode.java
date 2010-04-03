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

import java.util.HashMap;

import org.mroy31.deejayd.common.rpc.DefaultRpcCallback;
import org.mroy31.deejayd.webui.medialist.WebradioRenderer;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.Widget;

public class WebradioMode extends WebuiMode implements ClickHandler {
    private Label description;
    private Button wbClear;
    private Button wbRemove;
    private Button goToCurrent;

    public WebradioMode(WebuiLayout ui) {
        super("webradio", ui, false, false);
        mediaList.setOption(true, new WebradioRenderer(ui, "webradio"));
    }

    @Override
    public void onStatusChange(HashMap<String, String> status) {
        super.onStatusChange(status);
        boolean en = status.get("webradiosource").equals("local");
        wbClear.setEnabled(en);
        wbRemove.setEnabled(en);
    }

    @Override
    void buildTopToolbar(HorizontalPanel toolbar) {
        description = new Label();
        toolbar.setHorizontalAlignment(HorizontalPanel.ALIGN_RIGHT);
        toolbar.add(description);
    }

    @Override
    public void buildBottomToolbar(HorizontalPanel toolbar) {
        if (wbClear == null) {
            wbClear = new Button(ui.i18nConstants.clear());
            wbClear.setStyleName(
                    ui.resources.webuiCss().modeToolbarButton() + " " +
                    ui.resources.webuiCss().clearButton());
            wbClear.addClickHandler(this);
        }
        toolbar.add(wbClear);

        if (wbRemove == null) {
            wbRemove = new Button(ui.i18nConstants.remove());
            wbRemove.setStyleName(
                    ui.resources.webuiCss().modeToolbarButton() + " " +
                    ui.resources.webuiCss().removeButton());
            wbRemove.addClickHandler(this);
        }
        toolbar.add(wbRemove);

        if (goToCurrent == null) {
            goToCurrent = new Button(ui.i18nConstants.wbGoCurrent());
            goToCurrent.setStyleName(
                    ui.resources.webuiCss().modeToolbarButton() + " " +
                    ui.resources.webuiCss().gotoButton());
            goToCurrent.addClickHandler(this);
        }
        toolbar.add(goToCurrent);
    }

    @Override
    void setDescription(int length, int timelength) {
        if (description != null) {
            description.setText(ui.i18nMessages.webradiosDesc(length));
        }
    }

    public void onClick(ClickEvent event) {
        Widget sender = (Widget) event.getSource();
        if (sender == wbClear) {
            ui.rpc.wbModeClear(new DefaultRpcCallback(ui));
        } else if (sender == wbRemove) {
            ui.rpc.wbModeRemove(mediaList.getSelection(),
                    new DefaultRpcCallback(ui));
        } else if (sender == goToCurrent) {
            if (currentPlayingPos != -1) {
                mediaList.goTo(currentPlayingPos);
            }
        }
    }
}

//vim: ts=4 sw=4 expandtab