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

import org.mroy31.deejayd.common.rpc.DefaultRpcCallback;
import org.mroy31.deejayd.common.widgets.DeejaydUtils;
import org.mroy31.deejayd.mobile.client.SourcePanel;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Widget;


public class PlaylistMode extends DefaultDeejaydMode {
    private OptionPanel optionPanel = new OptionPanel("playlist", hideCtxCmd);

    public PlaylistMode(SourcePanel manager) {
        super("playlist", manager);
    }

    @Override
    public MediaList initMediaList() {
        return new MediaList("playlist", new MediaListFormater() {
            @Override
            public Widget formatRow(JSONObject media) {
                String title = media.get("title").isString().stringValue() +
                        " ("+DeejaydUtils.formatTime(Integer.parseInt(
                             media.get("length").isString().stringValue()))+")";
                String desc = "";
                JSONString artist = media.get("artist").isString();
                JSONString album = media.get("album").isString();
                if (artist != null) {
                    desc += artist.stringValue()+" - ";
                }
                if (album != null) {
                    desc += "<b>"+album.stringValue()+"<b>";
                }
                return new MediaItem(
                        (int) media.get("id").isNumber().doubleValue(),
                        title, desc);
            }
        });
    }

    @Override
    public String getTitle() {
        return ui.i18nConst.playlist();
    }

    @Override
    public void initToolbar(HorizontalPanel toolbar) {
        Button option = new Button();
        option.addStyleName(ui.resources.mobileCss().playerButton());
        option.addStyleName(ui.resources.mobileCss().option());
        option.addClickHandler(new ClickHandler() {
            @Override
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
            @Override
            public void onClick(ClickEvent event) {
                manager.setContextWidget(ui.i18nConst.addFiles(),
                        new AudioLibrary());
                manager.setContextVisible(true);
            }
        });
        toolbar.add(loadFiles);

        Button clear = new Button();
        clear.addStyleName(ui.resources.mobileCss().playerButton());
        clear.addStyleName(ui.resources.mobileCss().clear());
        clear.addClickHandler(new ClickHandler() {
            @Override
            public void onClick(ClickEvent event) {
                ui.rpc.plsModeClear(new DefaultRpcCallback(ui));
            }
        });
        toolbar.add(clear);

        Button shuffle = new Button();
        shuffle.addStyleName(ui.resources.mobileCss().playerButton());
        shuffle.addStyleName(ui.resources.mobileCss().shuffle());
        shuffle.addClickHandler(new ClickHandler() {
            @Override
            public void onClick(ClickEvent event) {
                ui.rpc.plsModeShuffle(new DefaultRpcCallback(ui));
            }
        });
        toolbar.add(shuffle);
    }
}

//vim: ts=4 sw=4 expandtab