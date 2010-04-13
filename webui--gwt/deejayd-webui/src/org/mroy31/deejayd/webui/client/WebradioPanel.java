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

import org.mroy31.deejayd.common.events.StatusChangeEvent;
import org.mroy31.deejayd.common.events.StatusChangeHandler;
import org.mroy31.deejayd.common.rpc.DefaultRpcCallback;
import org.mroy31.deejayd.common.rpc.GenericRpcCallback;
import org.mroy31.deejayd.common.widgets.DeejaydUIWidget;
import org.mroy31.deejayd.webui.resources.WebuiResources;
import org.mroy31.deejayd.webui.widgets.LoadingWidget;

import com.google.gwt.core.client.GWT;
import com.google.gwt.dom.client.Element;
import com.google.gwt.event.dom.client.ChangeEvent;
import com.google.gwt.event.dom.client.ChangeHandler;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.http.client.Request;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiFactory;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.DOM;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.DeckPanel;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.ListBox;
import com.google.gwt.user.client.ui.ScrollPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.google.gwt.user.client.ui.Widget;

public class WebradioPanel extends WebuiPanel implements StatusChangeHandler {

    private static WebradioPanelUiBinder uiBinder = GWT
            .create(WebradioPanelUiBinder.class);

    interface WebradioPanelUiBinder extends UiBinder<Widget, WebradioPanel> { }

    @UiField HorizontalPanel panelHeader;
    @UiField Label panelTitle;
    @UiField ListBox sourceListBox;
    @UiField DeckPanel deckPanel;
    @UiField HorizontalPanel categoriesToolbar;
    @UiField ScrollPanel categoriesScrollPanel;
    @UiField VerticalPanel categoriesList;
    @UiField Label categoriesTitle;

    @UiField HorizontalPanel formTitlePanel;
    @UiField Label formTitle;
    @UiField Label nameLabel;
    @UiField TextBox nameInput;
    @UiField Label urlLabel;
    @UiField TextBox urlInput;
    @UiField HorizontalPanel buttonPanel;
    @UiField Button addButton;
    @UiField(provided = true) final WebuiResources resources;

    private WebuiLayout ui;
    private String source = null;
    private String categorie = null;
    private HashMap<String, Boolean> sourceList = new HashMap<String, Boolean>();

    private class SourceRpcCallback extends GenericRpcCallback {
        public SourceRpcCallback(DeejaydUIWidget ui) { super(ui); }

        @Override
        protected void onJSONRPCError(Request request, String code, String msg){
            super.onJSONRPCError(request, code, msg);
            // set source to default value
            updatePanel();
        }

        @Override
        public void onCorrectAnswer(JSONValue data) {
            ui.update();
        }
    }

    private class OnSourceChange implements ChangeHandler {
        private WebuiLayout ui;

        public OnSourceChange(WebuiLayout webui) {
            ui = webui;
        }

        @Override
        public void onChange(ChangeEvent event) {
            String source = sourceListBox.getValue(
                    sourceListBox.getSelectedIndex());
            ui.rpc.wbModeSetSource(source, new SourceRpcCallback(ui));
        }
    }

    private class WbAddCallback extends GenericRpcCallback {
        public WbAddCallback(DeejaydUIWidget ui) {super(ui);}
        public void onCorrectAnswer(JSONValue data) {
            nameInput.setValue("");
            urlInput.setValue("");
            ui.update();
        }
    }

    private class WbSourceListCallback extends GenericRpcCallback {
        public WbSourceListCallback(WebuiLayout ui) {super(ui);}
        public void onCorrectAnswer(JSONValue data) {
            JSONObject list = data.isObject();
            for (String key : list.keySet()) {
                boolean hasCat = list.get(key).isBoolean().booleanValue();
                sourceList.put(key, hasCat);
                sourceListBox.addItem(getSourceName(key), key);
            }
            sourceListBox.addChangeHandler(new OnSourceChange((WebuiLayout)ui));
            updatePanel();
        }
    }

    private class SelectCatHandler implements ClickHandler {
        private WebuiLayout ui;
        private String value;

        public SelectCatHandler(WebuiLayout webui, String value) {
            this.value = value;
            this.ui = webui;
        }

        @Override
        public void onClick(ClickEvent event) {
            this.ui.rpc.wbModeSetSourceCategorie(value,
                    new DefaultRpcCallback(ui));
        }

    }

    private class WbCategoriesListCallback extends GenericRpcCallback {
        public WbCategoriesListCallback(WebuiLayout ui) {super(ui);}
        public void onCorrectAnswer(JSONValue data) {
            categoriesList.clear();
            JSONArray list = data.isArray();
            Label currentCat = null;
            for (int idx=0; idx<list.size(); idx++) {
                String cat = list.get(idx).isString().stringValue();
                Label lab = new Label(cat);
                lab.getElement().setId("wb-cat-"+cat);
                lab.addStyleName(resources.webuiCss().wbCategorieItem());
                if ((idx%2) == 0) {
                    lab.addStyleName(resources.webuiCss().oddRow());
                }
                if (cat.equals(categorie)) {
                    currentCat = lab;
                    lab.addStyleName(resources.webuiCss().currentItem());
                }
                lab.addClickHandler(new SelectCatHandler((WebuiLayout)ui, cat));
                categoriesList.add(lab);
            }

            if (currentCat != null) {
                categoriesScrollPanel.ensureVisible(currentCat);
            }
        }
    }


    /**
     * WebuiPanel constructor
     * @param webui
     */
    public WebradioPanel(WebuiLayout webui) {
        super("webradio");
        resources = webui.resources;
        ui = webui;
        initWidget(uiBinder.createAndBindUi(this));

        panelHeader.setCellVerticalAlignment(panelTitle,
                HorizontalPanel.ALIGN_MIDDLE);
        panelTitle.setText(ui.i18nConstants.wbCurrentSource());

        categoriesToolbar.setCellHorizontalAlignment(categoriesTitle,
                HorizontalPanel.ALIGN_CENTER);
        categoriesToolbar.setCellVerticalAlignment(categoriesTitle,
                HorizontalPanel.ALIGN_MIDDLE);
        categoriesTitle.setText(ui.i18nConstants.wbCategories());

        formTitlePanel.setCellHorizontalAlignment(formTitle,
                HorizontalPanel.ALIGN_CENTER);
        formTitlePanel.setCellVerticalAlignment(formTitle,
                HorizontalPanel.ALIGN_MIDDLE);
        formTitle.setText(ui.i18nConstants.wbAdd());
        nameLabel.setText(ui.i18nConstants.wbName());
        urlLabel.setText(ui.i18nConstants.wbUrl());

        buttonPanel.setCellHorizontalAlignment(addButton,
                HorizontalPanel.ALIGN_RIGHT);
        addButton.setText(ui.i18nConstants.add());
        addButton.addClickHandler(new ClickHandler() {
            @Override
            public void onClick(ClickEvent event) {
                String name = nameInput.getValue();
                String url = urlInput.getValue();
                if (!name.equals("") && !url.equals("")) {
                    ui.rpc.wbModeAdd(name, url, new WbAddCallback(ui));
                }
            }
        });

        ui.addStatusChangeHandler(this);
    }


    @UiFactory public TextBox makeWbTextBox() {
        TextBox box = new TextBox();
        box.setVisibleLength(12);
        box.setMaxLength(128);

        return box;
    }

    @Override
    public void onStatusChange(StatusChangeEvent event) {
        HashMap<String, String> status = event.getStatus();
        if (source == null) {
            // add current source in sourceList
            source = status.get("webradiosource");
            categorie = status.get("webradiosourcecat");
            ui.rpc.wbModeGetSources(new WbSourceListCallback(ui));
        } else if (!source.equals(status.get("webradiosource"))) {
            source = status.get("webradiosource");
            categorie = status.get("webradiosourcecat");
            updatePanel();
        } else if (sourceList.get(source) &&
                !status.get("webradiosourcecat").equals(categorie)) {
            // Select current category
            if (categorie != null) {
                Element elt = DOM.getElementById("wb-cat-"+categorie);
                if (elt != null)
                    elt.removeClassName(resources.webuiCss().currentItem());
            }
            categorie = status.get("webradiosourcecat");
            Element elt = DOM.getElementById("wb-cat-"+categorie);
            if (elt != null)
                elt.addClassName(resources.webuiCss().currentItem());
        }

        if (source.equals("local")) {
            deckPanel.showWidget(0);
        } else {
            deckPanel.showWidget(1);
        }
    }

    private void updatePanel() {
        if (!source.equals(
                sourceListBox.getValue(sourceListBox.getSelectedIndex()))) {
            for (int idx=0; idx<sourceListBox.getItemCount(); idx ++) {
                if (source.equals(sourceListBox.getValue(idx))) {
                    sourceListBox.setSelectedIndex(idx);
                    break;
                }
            }
        }

        if (sourceList.get(source)) { // source has categories, get them
            categoriesList.clear();
            categoriesList.add(new LoadingWidget(
                    ui.i18nConstants.wbLoadingCategories(), resources));
            ui.rpc.wbModeGetSourceCategories(source,
                    new WbCategoriesListCallback(ui));
        }
    }

    private String getSourceName(String sourceName) {
        if (sourceName.equals("local")) {
            return ui.i18nConstants.wbLocalSource();
        } else if (sourceName.equals("shoutcast")) {
            return ui.i18nConstants.wbShoutcastSource();
        }
        return "";
    }
}

//vim: ts=4 sw=4 expandtab