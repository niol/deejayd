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

import org.mroy31.deejayd.common.events.LibraryChangeEvent;
import org.mroy31.deejayd.common.events.LibraryChangeHandler;
import org.mroy31.deejayd.common.rpc.DefaultRpcCallback;
import org.mroy31.deejayd.common.rpc.GenericRpcCallback;
import org.mroy31.deejayd.webui.resources.WebuiResources;
import org.mroy31.deejayd.webui.widgets.LibraryManager;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.dom.client.FocusEvent;
import com.google.gwt.event.dom.client.FocusHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.DOM;
import com.google.gwt.user.client.Event;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.Tree;
import com.google.gwt.user.client.ui.TreeItem;
import com.google.gwt.user.client.ui.Widget;

public class VideoPanel extends WebuiPanel
        implements ClickHandler, LibraryChangeHandler {
    private WebuiLayout ui;

    private static VideoPanelUiBinder uiBinder = GWT
            .create(VideoPanelUiBinder.class);
    interface VideoPanelUiBinder extends UiBinder<Widget, VideoPanel> {}


    private class VideoTreeItem extends Composite {
        private String path;

        public VideoTreeItem(String dir, String root) {
            this(dir, dir, root);
        }

        public VideoTreeItem(String title, String dir, String root) {
            path = root.equals("") ? dir : root+"/"+dir;
            HorizontalPanel panel = new HorizontalPanel();
            panel.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);

            panel.add(new Image(resources.folder()));
            Label lab = new Label(title, false);
            DOM.setStyleAttribute(lab.getElement(), "paddingLeft", "5px");
            panel.add(lab);

            initWidget(panel);
            sinkEvents(Event.ONCLICK);
        }

        @Override
        public void onBrowserEvent(Event event) {
          super.onBrowserEvent(event);
          switch (DOM.eventGetType(event)) {
              case Event.ONCLICK:
                  ui.rpc.videoModeSet(getPath(), "directory",
                        new DefaultRpcCallback(ui));
                  break;
          }
        }

        public String getPath() {
            return path;
        }
    }

    @UiField(provided = true) final LibraryManager updateButton;
    @UiField HorizontalPanel northPanel;
    @UiField HorizontalPanel southPanel;
    @UiField HorizontalPanel searchPanel;
    @UiField TextBox searchEntry;
    @UiField Button searchButton;
    @UiField Tree videoTree;
    @UiField(provided = true) final WebuiResources resources;

    public VideoPanel(WebuiLayout webui) {
        super("video");
        this.resources = webui.resources;
        this.updateButton = webui.videoLibrary;
        this.ui = webui;

        initWidget(uiBinder.createAndBindUi(this));
        northPanel.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);
        Label title = new Label(ui.i18nConstants.videoDirectories());
        title.addStyleName(resources.webuiCss().italic());
        DOM.setStyleAttribute(title.getElement(), "paddingLeft", "5px");
        northPanel.add(title);
        southPanel.setCellHorizontalAlignment(searchPanel,
                HorizontalPanel.ALIGN_RIGHT);
        searchEntry.setVisibleLength(12);
        searchEntry.addFocusHandler(new FocusHandler() {
            @Override
            public void onFocus(FocusEvent event) {
                searchEntry.setSelectionRange(0,
                        searchEntry.getValue().length());
            }
        });
        searchButton.setText(ui.i18nConstants.search());
        searchButton.addClickHandler(this);

        ui.videoLibrary.addLibraryChangeHandler(this);
        buildTree();
    }

    @Override
    public void onClick(ClickEvent event) {
        Widget source = (Widget) event.getSource();
        if (source == searchButton) {
            if (!searchEntry.getValue().equals("")) {
                ui.rpc.videoModeSet(searchEntry.getValue(), "search",
                        new DefaultRpcCallback(ui));
            }
        }
    }

    @Override
    public void onLibraryChange(LibraryChangeEvent event) {
        buildTree();
    }

    private void buildTree() {
        videoTree.clear();
        TreeItem rootItem = new TreeItem(new VideoTreeItem("/", "", ""));
        videoTree.addItem(rootItem);
        buildTree("", rootItem);
    }

    private void buildTree(final String rPath, final TreeItem parent) {
        ui.rpc.libGetDirectory("video", rPath, new GenericRpcCallback() {

            @Override
            public void setError(String error) {
                ui.setError(error);
            }

            @Override
            public void onCorrectAnswer(JSONValue data) {
                JSONArray dirs = data.isObject().get("directories").isArray();
                for (int idx=0; idx<dirs.size(); idx++) {
                    String d = dirs.get(idx).isString().stringValue();
                    TreeItem item = new TreeItem(new VideoTreeItem(d, rPath));
                    parent.addItem(item);

                    String path = rPath.equals("") ? d : rPath+"/"+d;
                    buildTree(path, item);
                }
            }
        });
    }
}

//vim: ts=4 sw=4 expandtab