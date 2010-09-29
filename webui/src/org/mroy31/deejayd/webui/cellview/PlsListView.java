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

import org.mroy31.deejayd.common.provider.RecordPlsProvider;
import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.common.rpc.types.Playlist;
import org.mroy31.deejayd.webui.cellview.columns.GrippyCell;
import org.mroy31.deejayd.webui.cellview.columns.GrippyColumn;
import org.mroy31.deejayd.webui.client.WebuiLayout;
import org.mroy31.deejayd.webui.resources.WebuiResources;

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
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.ScrollPanel;
import com.google.gwt.user.client.ui.Widget;
import com.google.gwt.view.client.ProvidesKey;
import com.google.gwt.view.client.RangeChangeEvent;

public class PlsListView extends Composite {
    private final WebuiLayout ui;

    private static PlsListViewUiBinder uiBinder = GWT
            .create(PlsListViewUiBinder.class);

    interface PlsListViewUiBinder extends UiBinder<Widget, PlsListView> {
    }

    @UiField(provided = true) DeejaydCellTable<Playlist> list;
    @UiField ScrollPanel listPanel;
    @UiField Button loadButton;
    @UiField Button loadQueueButton;
    @UiField Button removeButton;
    @UiField CheckBox selectAll;
    @UiField(provided = true) final WebuiResources resources;

    private int PAGE_SIZE = 500;
    private DeejaydSelModel<Playlist> selModel = new DeejaydSelModel<Playlist>();
    private RecordPlsProvider provider;

    public PlsListView(WebuiLayout webui) {
        this.ui = webui;
        this.resources = webui.resources;

        list = new DeejaydCellTable<Playlist>(PAGE_SIZE);
        list.setKeyProvider(new ProvidesKey<Playlist>() {

            public Object getKey(Playlist item) {
                return Integer.toString(item.getId());
            }
        });
        list.addRangeChangeHandler(new RangeChangeEvent.Handler() {

            public void onRangeChange(RangeChangeEvent event) {
                listPanel.scrollToTop();
            }
        });

        provider = new RecordPlsProvider(ui);
        provider.getDataProvider().addDataDisplay(list);
        list.setSelectionModel(selModel);
        initWidget(uiBinder.createAndBindUi(this));

        loadButton.setText(ui.i18nConstants.add());
        loadQueueButton.setText(ui.i18nConstants.addQueue());
        removeButton.setText(ui.i18nConstants.remove());

     // add columns
        list.addColumn(new GrippyColumn<Playlist>("recpls", list,
                ui.resources.webuiCss().grippyCell(),
                new GrippyCell.DragStartMessage() {

                    public String onDragStart(int count) {
                        return ui.i18nMessages.plsCount(count);
                    }
        }));
        list.setColumnWidth(0, "20px");

        list.addColumn(new Column<Playlist, ImageResource>(
                new ImageResourceCell()) {

            @Override
            public ImageResource getValue(Playlist object) {
                if (object.getType().equals("static"))
                    return ui.resources.playlist();
                else
                    return ui.resources.magicPlaylist();
            }

        });
        list.setColumnWidth(1, "30px");

        list.addColumn(new TextColumn<Playlist>() {

            @Override
            public String getValue(Playlist object) {
                return object.getName();
            }
        });

        provider.onPlsListChange(null);
    }

    @UiHandler("loadButton")
    public void loadButtonHandler(ClickEvent event) {
        ui.rpc.plsModeLoadPls(getSelection(), -1, new AnswerHandler<Boolean>() {

            public void onAnswer(Boolean answer) {
                ui.update();
                selModel.clearSelection();
                selectAll.setValue(false, false);
            }
        });
    }

    @UiHandler("loadQueueButton")
    public void loadQueueButtonHandler(ClickEvent event) {
        ui.rpc.queueModeLoadPls(getSelection(), -1, new AnswerHandler<Boolean>() {

            public void onAnswer(Boolean answer) {
                ui.update();
                selModel.clearSelection();
                selectAll.setValue(false, false);
            }
        });
    }

    @UiHandler("removeButton")
    public void removeButtonHandler(ClickEvent event) {
        List<String> sel = getSelection();
        if (sel.size() > 0) {
            boolean confirm = Window.confirm(
                    ui.i18nMessages.plsEraseConfirm(sel.size()));
            if (confirm) {
                ui.rpc.recPlsErase(sel, new AnswerHandler<Boolean>() {

                    public void onAnswer(Boolean answer) {
                        ui.updatePlsList();
                    }
                });
            }
        }
    }

    @UiHandler("selectAll")
    public void selectAllHandler(ValueChangeEvent<Boolean> event) {
        selModel.setSelected(list.getDisplayedItems(), event.getValue());
    }

    private List<String> getSelection() {
        ArrayList<String> sel = new ArrayList<String>();
        if (selModel != null) {
            for (Playlist item : list.getDisplayedItems()) {
                if (selModel.isSelected(item))
                    sel.add(Integer.toString(item.getId()));
            }
        }
        return sel;
    }
}

//vim: ts=4 sw=4 expandtab