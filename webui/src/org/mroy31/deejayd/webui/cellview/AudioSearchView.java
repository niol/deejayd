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

package org.mroy31.deejayd.webui.cellview;

import java.util.ArrayList;
import java.util.List;

import org.mroy31.deejayd.common.provider.LibrarySearchProvider;
import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.common.rpc.types.Media;
import org.mroy31.deejayd.webui.cellview.columns.GrippyColumn;
import org.mroy31.deejayd.webui.client.WebuiLayout;
import org.mroy31.deejayd.webui.resources.WebuiResources;

import com.google.gwt.cell.client.CheckboxCell;
import com.google.gwt.cell.client.FieldUpdater;
import com.google.gwt.cell.client.ImageResourceCell;
import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.resources.client.ImageResource;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.uibinder.client.UiHandler;
import com.google.gwt.user.cellview.client.Column;
import com.google.gwt.user.cellview.client.DeejaydCellTable;
import com.google.gwt.user.cellview.client.TextColumn;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.ListBox;
import com.google.gwt.user.client.ui.ScrollPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.Widget;
import com.google.gwt.view.client.ProvidesKey;
import com.google.gwt.view.client.RangeChangeEvent;

public class AudioSearchView extends Composite {
    private WebuiLayout ui;

    private static AudioSearchViewUiBinder uiBinder = GWT
            .create(AudioSearchViewUiBinder.class);

    interface AudioSearchViewUiBinder extends UiBinder<Widget, AudioSearchView> {
    }

    @UiField CheckBox selectAll;
    @UiField(provided = true) DeejaydCellTable<Media> list;
    @UiField ScrollPanel listPanel;
    @UiField TextBox pattern;
    @UiField ListBox type;
    @UiField Button searchButton;
    @UiField Button loadButton;
    @UiField Button loadQueueButton;
    @UiField Button clearButton;
    @UiField(provided = true) final WebuiResources resources;

    private int PAGE_SIZE = 500;
    private DeejaydSelModel<Media> selModel = new DeejaydSelModel<Media>();
    private LibrarySearchProvider provider;

    public AudioSearchView(WebuiLayout webui) {
        this.ui = webui;
        this.resources = ui.resources;

        list = new DeejaydCellTable<Media>(PAGE_SIZE);
        list.setKeyProvider(new ProvidesKey<Media>() {

            public Object getKey(Media item) {
                return item.getStrAttr("media_id");
            }
        });
        list.addRangeChangeHandler(new RangeChangeEvent.Handler() {

            public void onRangeChange(RangeChangeEvent event) {
                listPanel.scrollToTop();
            }
        });

        provider = new LibrarySearchProvider(ui, "audio");
        provider.getDataProvider().addDataDisplay(list);
        list.setSelectionModel(selModel);
        initWidget(uiBinder.createAndBindUi(this));

        searchButton.setText(ui.i18nConstants.search());
        pattern.setVisibleLength(12);
        type.addItem(ui.i18nConstants.all(), "all");
        type.addItem(ui.i18nConstants.title(), "title");
        type.addItem(ui.i18nConstants.artist(), "artist");
        type.addItem(ui.i18nConstants.album(), "album");
        loadButton.setText(ui.i18nConstants.add());
        loadQueueButton.setText(ui.i18nConstants.addQueue());
        clearButton.setText(ui.i18nConstants.clearSearch());

     // add columns
        list.addColumn(new GrippyColumn<Media>("audiosearch", list,
                ui.resources.drag()));
        list.setColumnWidth(0, "15px");

        final Column<Media, Boolean> checkColumn = new Column<Media, Boolean>(
                new CheckboxCell(true)) {

            @Override
            public Boolean getValue(Media object) {
                return selModel.isSelected(object);
              }
        };
        checkColumn.setFieldUpdater(new FieldUpdater<Media, Boolean>() {

            public void update(int index, Media object, Boolean value) {
                // Called when the user clicks on a checkbox.
                selModel.setSelected(object, value);
            }
        });
        list.addColumn(checkColumn);
        list.setColumnWidth(1, "30px");

        list.addColumn(new Column<Media, ImageResource>(
                new ImageResourceCell()) {

            @Override
            public ImageResource getValue(Media object) {
                return ui.resources.audio();
            }

        });
        list.setColumnWidth(2, "30px");

        list.addColumn(new TextColumn<Media>() {

            @Override
            public String getValue(Media object) {
                return object.getStrAttr("filename");
            }
        });
    }

    public void focus() {
        pattern.setFocus(true);
        pattern.selectAll();
    }

    @UiHandler("searchButton")
    public void searchButtonHandler(ClickEvent event) {
        String value = pattern.getValue();
        if (value != "") {
            provider.search(value, type.getValue(type.getSelectedIndex()));
        }
    }

    @UiHandler("clearButton")
    public void clearButtonHandler(ClickEvent event) {
        provider.clear();
        pattern.setValue("", false);
        selectAll.setValue(false, false);
    }

    @UiHandler("loadButton")
    public void loadButtonHandler(ClickEvent event) {
        ui.rpc.plsModeLoadIds(getSelection(), -1, new AnswerHandler<Boolean>() {

            public void onAnswer(Boolean answer) {
                ui.update();
                selModel.clearSelection();
                selectAll.setValue(false, false);
            }
        });
    }

    @UiHandler("loadQueueButton")
    public void loadQueueButtonHandler(ClickEvent event) {
        ui.rpc.queueLoadIds(getSelection(), -1, new AnswerHandler<Boolean>() {

            public void onAnswer(Boolean answer) {
                ui.update();
                selModel.clearSelection();
                selectAll.setValue(false, false);
            }
        });
    }

    @UiHandler("selectAll")
    public void selectAllHandler(ValueChangeEvent<Boolean> event) {
        selModel.setSelected(list.getDisplayedItems(), event.getValue());
    }

    private List<String> getSelection() {
        ArrayList<String> sel = new ArrayList<String>();
        if (selModel != null) {
            for (Media item : list.getDisplayedItems()) {
                if (selModel.isSelected(item))
                    sel.add(item.getStrAttr("media_id"));
            }
        }
        return sel;
    }
}

//vim: ts=4 sw=4 expandtab