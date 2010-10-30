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
import java.util.List;

import org.mroy31.deejayd.common.events.StatusChangeEvent;
import org.mroy31.deejayd.common.rpc.callbacks.AbstractRpcCallback;
import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.common.rpc.types.MediaFilter;
import org.mroy31.deejayd.common.widgets.DeejaydUtils;
import org.mroy31.deejayd.webui.cellview.AbstractMediaList;
import org.mroy31.deejayd.webui.cellview.Pager;
import org.mroy31.deejayd.webui.cellview.SortSongList;
import org.mroy31.deejayd.webui.resources.WebuiResources;
import org.mroy31.deejayd.webui.widgets.RatingButton;
import org.mroy31.deejayd.webui.widgets.TagList;
import org.mroy31.deejayd.webui.widgets.WebuiSplitLayoutPanel;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ChangeEvent;
import com.google.gwt.event.dom.client.ChangeHandler;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.dom.client.KeyPressEvent;
import com.google.gwt.event.dom.client.KeyPressHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiFactory;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.DOM;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.DockLayoutPanel;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.ListBox;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.Widget;

public class NavigationPanelMode extends AbstractWebuiMode implements ClickHandler {
    private HashMap<String, TagList> tagMap = new HashMap<String, TagList>();
    private String currentSource = "";
    private String updatedTag = null;

    private static NavigationPanelModeUiBinder uiBinder = GWT
            .create(NavigationPanelModeUiBinder.class);
    interface NavigationPanelModeUiBinder extends
            UiBinder<Widget, NavigationPanelMode> {}

    private class TagChangeHandler implements ValueChangeHandler<List<String>> {
        private String tag;
        public TagChangeHandler(String tag) {this.tag = tag; }

        public void onValueChange(ValueChangeEvent<List<String>> event) {
            updatedTag = tag;
            List<String> value = event.getValue();
            if (value.get(0).equals("__all__")) {
                ui.rpc.panelModeRemoveFilter(tag, null);
            } else {
                ui.rpc.panelModeSetFilter(tag, value, null);
            }
        }
    }

    private Timer searchTimer = new Timer() {
        @Override
        public void run() {
            updateSearch();
        }
    };

    @UiField DockLayoutPanel mainPanel;
    @UiField HorizontalPanel bottomToolbar;
    @UiField HorizontalPanel leftBottomToolbar;
    @UiField HorizontalPanel rightBottomToolbar;
    @UiField HorizontalPanel topToolbar;
    @UiField TextBox searchPattern;
    @UiField ListBox searchType;
    @UiField Button searchClearButton;
    @UiField Button chooseAllButton;
    @UiField Label descLabel;
    @UiField Button goToCurrent;
    @UiField(provided = true) final RatingButton ratingButton;
    @UiField(provided = true) final Pager pager;
    @UiField(provided = true) final WebuiResources resources;
    HorizontalPanel tagListPanel = new HorizontalPanel();
    WebuiSplitLayoutPanel panelLayout = new WebuiSplitLayoutPanel();
    AbstractMediaList mediaList;

    public NavigationPanelMode(WebuiLayout webui) {
        super("panel", webui, true, true);
        this.resources = webui.resources;
        this.pager = new Pager(webui);
        mediaList = new SortSongList(ui, "panel", AbstractMediaList.DEFAULT_PAGE_SIZE);
        ratingButton = new RatingButton(ui, mediaList.getSelectionModel());

        initWidget(uiBinder.createAndBindUi(this));
        panelLayout.addNorth(tagListPanel, 150);
        tagListPanel.setWidth("100%"); tagListPanel.setHeight("100%");
        mediaList.setPager(pager);
        panelLayout.add(mediaList);
        mainPanel.add(panelLayout);


        topToolbar.setCellHorizontalAlignment(descLabel,
                HorizontalPanel.ALIGN_RIGHT);
        bottomToolbar.setCellHorizontalAlignment(rightBottomToolbar,
                HorizontalPanel.ALIGN_RIGHT);

        // build search toolbar
        searchType.addItem(ui.i18nConstants.all(), "all");
        searchType.addItem(ui.i18nConstants.title(), "title");
        searchType.addItem(ui.i18nConstants.artist(), "artist");
        searchType.addItem(ui.i18nConstants.album(), "album");
        searchType.addItem(ui.i18nConstants.genre(), "genre");
        searchType.addChangeHandler(new ChangeHandler() {
            public void onChange(ChangeEvent event) {
                updateSearch();
            }
        });
        searchClearButton.setText(ui.i18nConstants.clear());
        searchClearButton.addClickHandler(this);
        chooseAllButton.setText(ui.i18nConstants.chooseAll());
        chooseAllButton.addClickHandler(this);
        searchPattern.addKeyPressHandler(new KeyPressHandler() {
            public void onKeyPress(KeyPressEvent event) {
                searchTimer.cancel();
                searchTimer.schedule(300);
            }
        });

        // build bottom toolbar
        goToCurrent.setText(ui.i18nConstants.goCurrentSong());
        goToCurrent.addClickHandler(this);
        HorizontalPanel optionPanel = new HorizontalPanel();
        DOM.setStyleAttribute(optionPanel.getElement(), "paddingLeft", "4px");
        optionPanel.add(makePlayorderWidget());
        optionPanel.add(makeRepeatWidget());
        leftBottomToolbar.add(optionPanel);

        // load tag list
        ui.rpc.panelModeGetTags(new AnswerHandler<List<String>>() {

            public void onAnswer(List<String> answer) {
                for (String tag : answer) {
                    TagList tagW = new TagList((WebuiLayout) ui,
                            getTagPanelTitle(tag));
                    tagW.addValueChangeHandler(new TagChangeHandler(tag));
                    tagListPanel.add(tagW);
                    tagMap.put(tag, tagW);
                }
            }
        });
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

    @Override
    protected void setDescription(int length, int timelength) {
        if (length == 0) {
            descLabel.setText(ui.i18nMessages.songsDesc(length));
        } else {
            String timeDesc = DeejaydUtils.formatTimeLong(timelength,
                    ui.i18nMessages);
            descLabel.setText(ui.i18nMessages.songsDesc(length)+" ("+
                    timeDesc+")");
        }
    }

    public void onClick(ClickEvent event) {
        Widget sender = (Widget) event.getSource();
        if (sender == searchClearButton) {
            ui.rpc.panelModeClearSearch();
        } else if (sender == chooseAllButton) {
            ui.rpc.panelModeClearAll(null);
        } else if (sender == goToCurrent) {
            if (currentPlayingPos != -1) {
                mediaList.scrollTo(currentPlayingPos);
            }
        }
    }

    @Override
    public void onStatusChange(StatusChangeEvent event) {
        super.onStatusChange(event);

        ui.rpc.panelModeActiveList(new AnswerHandler<HashMap<String, String>>(){

            public void onAnswer(HashMap<String, String> answer) {
                String type = answer.get("type");
                if (!type.equals(currentSource)) {
                    int pos = type.equals("panel") ? 150 : 0;
                    panelLayout.setSplitPosition(tagListPanel, pos, false);
                    setSearchEnabled(type.equals("panel"));
                    currentSource = type;
                }

                if (type.equals("panel")) {
                    ui.rpc.panelModeBuildPanel(updatedTag,
                            new AbstractRpcCallback() {

                        @Override
                        public void onCorrectAnswer(JSONValue data) {
                            JSONObject ans = data.isObject();

                            // update search bar
                            if (ans.containsKey("search")) {
                                MediaFilter searchFilter = MediaFilter.parse(
                                        ans.get("search").isObject());
                                if (searchFilter.isBasic() != null ) {
                                    searchPattern.setValue(searchFilter
                                            .isBasic().getPattern());
                                    selectSearchType(searchFilter
                                            .isBasic().getTag());
                                } else if (searchFilter.isComplex() != null ) {
                                    MediaFilter f = searchFilter
                                            .isComplex().getFilters()[0];
                                    searchType.setSelectedIndex(0);
                                    searchPattern.setValue(f
                                            .isBasic().getPattern());
                                }
                            } else {
                                searchPattern.setValue("");
                                searchType.setSelectedIndex(0);
                            }

                            // update panel list
                            JSONObject list = ans.get("panels").isObject();
                            for (String tag : list.keySet()) {
                                JSONArray itemList = list.get(tag).isArray();
                                tagMap.get(tag).setItems(itemList);
                            }
                        }
                    });
                    updatedTag = null;
                }
            }
        });
    }

    private void updateSearch() {
        ui.rpc.panelModeSetSearch(
                searchType.getValue(searchType.getSelectedIndex()),
                    searchPattern.getValue(), null);
    }

    private void setSearchEnabled(boolean enabled) {
        searchType.setEnabled(enabled);
        searchPattern.setEnabled(enabled);
        searchClearButton.setEnabled(enabled);
        chooseAllButton.setEnabled(enabled);
    }

    private void selectSearchType(String tag) {
        for (int idx=0; idx<searchType.getItemCount(); idx++) {
            if (searchType.getValue(idx).equals(tag)) {
                searchType.setSelectedIndex(idx);
                break;
            }
        }
    }

    private String getTagPanelTitle(String tag) {
        if (tag.equals("genre"))
            return ui.i18nConstants.genre();
        else if (tag.equals("artist") || tag.equals("various_artist"))
            return ui.i18nConstants.artist();
        else if (tag.equals("album"))
            return ui.i18nConstants.album();
        return "";
    }
}

//vim: ts=4 sw=4 expandtab