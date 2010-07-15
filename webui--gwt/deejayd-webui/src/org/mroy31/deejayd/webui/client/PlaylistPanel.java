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
import org.mroy31.deejayd.common.widgets.DeejaydUIWidget;
import org.mroy31.deejayd.webui.resources.WebuiResources;
import org.mroy31.deejayd.webui.widgets.LibraryManager;
import org.mroy31.deejayd.webui.widgets.LoadingWidget;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.SelectionEvent;
import com.google.gwt.event.logical.shared.SelectionHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.HasVerticalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.ListBox;
import com.google.gwt.user.client.ui.TabLayoutPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.google.gwt.user.client.ui.Widget;

public class PlaylistPanel extends WebuiPanel
        implements ClickHandler, LibraryChangeHandler {

    private static PlaylistPanelUiBinder uiBinder = GWT
            .create(PlaylistPanelUiBinder.class);
    interface PlaylistPanelUiBinder extends UiBinder<Widget, PlaylistPanel> {}

    @UiField(provided = true) final LibraryManager updateButton;
    @UiField TabLayoutPanel tabPanel;
    @UiField Label dirHeader;
    @UiField Label searchHeader;
    @UiField Label plsHeader;
    @UiField CheckBox dirSelectAll;
    @UiField CheckBox searchSelectAll;
    @UiField CheckBox plsSelectAll;

    @UiField HorizontalPanel navBar;
    @UiField VerticalPanel dirPanel;
    @UiField VerticalPanel searchPanel;
    @UiField VerticalPanel plsPanel;

    @UiField TextBox searchPattern;
    @UiField ListBox searchType;
    @UiField Button searchButton;

    @UiField Button dirLoadButton;
    @UiField Button dirLoadQueueButton;
    @UiField Button searchLoadButton;
    @UiField Button searchLoadQueueButton;
    @UiField Button searchClearButton;
    @UiField Button plsLoadButton;
    @UiField Button plsLoadQueueButton;
    @UiField Button plsRemoveButton;
    @UiField(provided = true) final WebuiResources resources;

    private WebuiLayout ui;

    private interface PanelItem {
        public CheckBox getCheckBox();
        public String getValue();
    }

    private class PlaylistItem extends Composite implements PanelItem {
        private CheckBox ck;
        private String value;

        public PlaylistItem(String name, String type, int id) {
            this.value = Integer.toString(id);

            HorizontalPanel item = new HorizontalPanel();
            item.setVerticalAlignment(HasVerticalAlignment.ALIGN_MIDDLE);
            item.setSpacing(3);

            ck = new CheckBox();
            ck.setFormValue(value);
            item.add(ck);

            Image img = new Image(resources.playlist());
            if (type.equals("magic")) {
                img = new Image(resources.magicPlaylist());
            }
            item.add(img);

            item.add(new Label(name));
            initWidget(item);
        }

        public String getValue() {
            return value;
        }

        public CheckBox getCheckBox() {
            return ck;
        }
    }

    private class DirectoryItem extends Composite implements PanelItem {
        private String path;
        private CheckBox ck;

        public DirectoryItem(String dir, String root) {
            path = dir;
            if (!root.equals("")) {
                path = root + "/" + dir;
            }
            HorizontalPanel item = new HorizontalPanel();
            item.setVerticalAlignment(HasVerticalAlignment.ALIGN_MIDDLE);
            item.setSpacing(3);

            ck = new CheckBox();
            ck.setFormValue(path);
            item.add(ck);

            Image img = new Image(resources.folder());
            item.add(img);

            Label dirName = new Label(dir);
            dirName.addStyleName(resources.webuiCss().pointerCursor());
            dirName.addClickHandler(new ClickHandler() {
                public void onClick(ClickEvent event) {
                    buildDirFileList(path);
                }
            });
            item.add(dirName);

            initWidget(item);
        }

        public String getValue() {
            return path;
        }

        public CheckBox getCheckBox() {
            return ck;
        }
    }

    private class AudioItem extends Composite implements PanelItem {
        private String value;
        private CheckBox ck;

        public AudioItem(String fileName, String root) {
            value = fileName;
            if (!root.equals("")) {
                value = root + "/" + fileName;
            }

            HorizontalPanel item = buildItem(fileName);
            initWidget(item);
        }

        public AudioItem(String fileName, int mediaId) {
            value = Integer.toString(mediaId);

            HorizontalPanel item = buildItem(fileName);
            initWidget(item);
        }

        public CheckBox getCheckBox() {
            return ck;
        }

        public String getValue() {
            return value;
        }

        private HorizontalPanel buildItem(String fileName) {
            HorizontalPanel item = new HorizontalPanel();
            item.setVerticalAlignment(HasVerticalAlignment.ALIGN_MIDDLE);
            item.setSpacing(3);

            ck = new CheckBox();
            ck.setFormValue(value);
            item.add(ck);

            Image img = new Image(resources.audio());
            item.add(img);

            item.add(new Label(fileName));

            return item;
        }
    }

    private class DirFileCallback extends DefaultRpcCallback {
        public DirFileCallback(DeejaydUIWidget ui) {	super(ui); }

        @Override
        public void onCorrectAnswer(JSONValue data) {
            JSONArray files = data.isObject().get("files").isArray();
            JSONArray dirs = data.isObject().get("directories").isArray();
            String root = data.isObject().get("root").isString().stringValue();

            // build root value
            navBar.clear();
            if (!root.equals("")) {
                class navClickHandler implements ClickHandler {
                    private int idx;
                    private String[] rootPart;

                    public navClickHandler(int idx, String[] rootPart) {
                        this.idx = idx;
                        this.rootPart = rootPart;
                    }

                    @Override
                    public void onClick(ClickEvent event) {
                        String path = "";
                        for (int j=0; j<idx+1 ; j++) {
                            if (path.equals("")) {
                                path = rootPart[j];
                            } else {
                                path += "/"+rootPart[j];
                            }
                        }
                        buildDirFileList(path);
                    }
                }
                String[] rootPart = root.split("/");
                // set root button
                Button rootButton = new Button(" / ");
                rootButton.addClickHandler(new navClickHandler(-1, rootPart));
                navBar.add(rootButton);
                for (int i=0; i<rootPart.length; i++) {
                    Button pathButton = new Button(rootPart[i]);
                    pathButton.addClickHandler(new navClickHandler(i, rootPart));
                    navBar.add(pathButton);
                }
            }

            dirPanel.clear();
            for (int i=0; i<dirs.size(); i++) {
                String dir = dirs.get(i).isString().stringValue();
                dirPanel.add(new DirectoryItem(dir, root));
            }

            for (int i=0; i<files.size(); i++) {
                String filename = files.get(i).isObject().get("filename")
                                    .isString().stringValue();
                dirPanel.add(new AudioItem(filename, root));
            }
        }

    }

    private class SearchCallback extends DefaultRpcCallback {
        public SearchCallback(DeejaydUIWidget ui) {	super(ui); }

        @Override
        public void onCorrectAnswer(JSONValue data) {
            JSONArray medias = data.isObject().get("medias").isArray();

            searchPanel.clear();
            for (int i=0; i<medias.size(); i++) {
                String filename = medias.get(i).isObject().get("filename")
                        .isString().stringValue();
                int mediaId = (int) medias.get(i).isObject().get("media_id")
                        .isNumber().doubleValue();
                searchPanel.add(new AudioItem(filename, mediaId));
            }
        }
    }

    private class PanelDefaultCallback extends DefaultRpcCallback {
        private VerticalPanel panel;
        public PanelDefaultCallback(DeejaydUIWidget ui, VerticalPanel panel) {
            super(ui);
            this.panel = panel;
        }

        @Override
        public void onCorrectAnswer(JSONValue data) {
            ui.update();
            // disable checkbox
            for (int idx=0; idx<panel.getWidgetCount(); idx++) {
                PanelItem item = (PanelItem) panel.getWidget(idx);
                item.getCheckBox().setValue(false);
            }
        }
    }

    private class PlsListCallback extends DefaultRpcCallback {
        public PlsListCallback(DeejaydUIWidget ui) {	super(ui); }

        @Override
        public void onCorrectAnswer(JSONValue data) {
            JSONArray list = data.isObject().get("medias").isArray();
            for (int i=0; i<list.size(); i++) {
                String plsName = list.get(i).isObject().get("name")
                        .isString().stringValue();
                String plsType = list.get(i).isObject().get("type")
                        .isString().stringValue();
                int plsId = (int) list.get(i).isObject().get("id")
                        .isNumber().doubleValue();
                plsPanel.add(new PlaylistItem(plsName, plsType, plsId));
            }
        }
    }

    private class PlsEraseCallback extends DefaultRpcCallback {
        public PlsEraseCallback(DeejaydUIWidget ui) { super(ui); }

        @Override
        public void onCorrectAnswer(JSONValue data) {
            buildPlsList();
        }
    }
/***************************************************************************/
/***************************************************************************/
    public PlaylistPanel(WebuiLayout webui) {
        super("playlist");

        this.resources = webui.resources;
        this.updateButton = webui.audioLibrary;
        this.ui = webui;

        initWidget(uiBinder.createAndBindUi(this));
        // set header label
        dirHeader.setText(ui.i18nConstants.directory());
        searchHeader.setText(ui.i18nConstants.search());
        plsHeader.setText(ui.i18nConstants.playlists());

        // set directory part
        dirLoadButton.setText(ui.i18nConstants.add());
        dirLoadButton.addClickHandler(this);
        dirLoadQueueButton.setText(ui.i18nConstants.addQueue());
        dirLoadQueueButton.addClickHandler(this);
        dirSelectAll.addClickHandler(new ClickHandler() {
            public void onClick(ClickEvent event) {
                boolean value = dirSelectAll.getValue();
                for (int idx=0; idx<dirPanel.getWidgetCount(); idx++) {
                    PanelItem pn = (PanelItem) dirPanel.getWidget(idx);
                    CheckBox ck = (CheckBox) pn.getCheckBox();
                    ck.setValue(value);
                }
            }
        });
        ui.audioLibrary.addLibraryChangeHandler(this);

        // set search part
        searchButton.setText(ui.i18nConstants.search());
        searchButton.addClickHandler(this);
        searchPattern.setVisibleLength(12);
        searchType.addItem(ui.i18nConstants.all(), "all");
        searchType.addItem(ui.i18nConstants.title(), "title");
        searchType.addItem(ui.i18nConstants.artist(), "artist");
        searchType.addItem(ui.i18nConstants.album(), "album");
        searchLoadButton.setText(ui.i18nConstants.add());
        searchLoadButton.addClickHandler(this);
        searchLoadQueueButton.setText(ui.i18nConstants.addQueue());
        searchLoadQueueButton.addClickHandler(this);
        searchClearButton.setText(ui.i18nConstants.clearSearch());
        searchClearButton.addClickHandler(this);
        searchSelectAll.addClickHandler(new ClickHandler() {
            public void onClick(ClickEvent event) {
                boolean value = searchSelectAll.getValue();
                for (int idx=0; idx<searchPanel.getWidgetCount(); idx++) {
                    PanelItem pn = (PanelItem) searchPanel.getWidget(idx);
                    CheckBox ck = (CheckBox) pn.getCheckBox();
                    ck.setValue(value);
                }
            }
        });

        // set pls part
        plsLoadButton.setText(ui.i18nConstants.add());
        plsLoadButton.addClickHandler(this);
        plsLoadQueueButton.setText(ui.i18nConstants.addQueue());
        plsLoadQueueButton.addClickHandler(this);
        plsRemoveButton.setText(ui.i18nConstants.remove());
        plsRemoveButton.addClickHandler(this);
        plsSelectAll.addClickHandler(new ClickHandler() {
            public void onClick(ClickEvent event) {
                boolean value = plsSelectAll.getValue();
                for (int idx=0; idx<plsPanel.getWidgetCount(); idx++) {
                    PanelItem pn = (PanelItem) plsPanel.getWidget(idx);
                    CheckBox ck = (CheckBox) pn.getCheckBox();
                    ck.setValue(value);
                }
            }
        });


        tabPanel.addSelectionHandler(new SelectionHandler<Integer>() {
            @Override
            public void onSelection(SelectionEvent<Integer> event) {
                if (event.getSelectedItem().equals(1)) {
                    searchPattern.setFocus(true);
                    searchPattern.selectAll();
                }
            }
        });

        buildDirFileList();
        buildPlsList();
    }


    @Override
    public void onLibraryChange(LibraryChangeEvent event) {
        buildDirFileList();
    }

    @Override
    public void onClick(ClickEvent event) {
        Widget source = (Widget) event.getSource();
        if (source == searchButton) {
            String pattern = searchPattern.getValue();
            if (pattern != "") {
                searchPanel.clear();
                searchPanel.add(new LoadingWidget(ui.i18nConstants.loading(),
                        resources));
                ui.rpc.libSearch("audio", pattern,
                        searchType.getValue(searchType.getSelectedIndex()),
                        new SearchCallback(ui));
            }
        } else if (source == dirLoadButton) {
            JSONArray sel = getSelection(dirPanel);
            if (sel.size() > 0) {
                ui.rpc.plsModeLoadPath(sel, -1, new PanelDefaultCallback(ui,
                        dirPanel));
            }
        } else if (source == dirLoadQueueButton) {
            JSONArray sel = getSelection(dirPanel);
            if (sel.size() > 0) {
                ui.rpc.queueLoadPath(sel, -1, new PanelDefaultCallback(ui,
                        dirPanel));
            }
        } else if (source == searchLoadButton) {
            JSONArray sel = getSelection(searchPanel);
            if (sel.size() > 0) {
                ui.rpc.plsModeLoadIds(sel, -1, new PanelDefaultCallback(ui,
                        searchPanel));
            }
        } else if (source == searchLoadQueueButton) {
            JSONArray sel = getSelection(searchPanel);
            if (sel.size() > 0) {
                ui.rpc.queueLoadPath(sel, -1, new PanelDefaultCallback(ui,
                        searchPanel));
            }
        } else if (source == searchClearButton) {
            searchPanel.clear();
            searchPattern.setValue("");
        } else if (source == plsLoadButton) {
            JSONArray sel = getSelection(plsPanel);
            if (sel.size() > 0) {
                ui.rpc.plsModeLoadPls(sel, -1, new PanelDefaultCallback(ui,
                        plsPanel));
            }
        } else if (source == plsLoadQueueButton) {
            JSONArray sel = getSelection(plsPanel);
            if (sel.size() > 0) {
                ui.rpc.queueModeLoadPls(sel, -1, new PanelDefaultCallback(ui,
                        plsPanel));
            }
        } else if (source == plsRemoveButton) {
            JSONArray sel = getSelection(plsPanel);
            if (sel.size() > 0) {
                boolean confirm = Window.confirm(
                        ui.i18nMessages.plsEraseConfirm(sel.size()));
                if (confirm) {
                    ui.rpc.recPlsErase(sel, new PlsEraseCallback(ui));
                }
            }
        }
    }

    public void buildPlsList() {
        plsPanel.clear();
        ui.rpc.recPlsList(new PlsListCallback(ui));
    }

    private void buildDirFileList() {
        buildDirFileList("");
    }

    private void buildDirFileList(String dir) {
        dirPanel.clear();
        dirPanel.add(new LoadingWidget(ui.i18nConstants.loading(), resources));
        ui.rpc.libGetDirectory("audio",
                dir, new DirFileCallback(ui));
    }

    private JSONArray getSelection(VerticalPanel panel) {
        JSONArray selection = new JSONArray();
        int i=0;
        for (int idx=0; idx<panel.getWidgetCount(); idx++) {
            PanelItem item = (PanelItem) panel.getWidget(idx);
            if (item.getCheckBox().getValue()) {
                selection.set(i, new JSONString(item.getValue()));
                i++;
            }
        }
        return selection;
    }
}

//vim: ts=4 sw=4 expandtab