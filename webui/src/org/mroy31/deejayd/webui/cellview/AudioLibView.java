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

import org.mroy31.deejayd.common.events.LibraryChangeEvent;
import org.mroy31.deejayd.common.events.LibraryChangeHandler;
import org.mroy31.deejayd.common.provider.LibraryProvider;
import org.mroy31.deejayd.common.provider.LibraryProvider.LibraryItem;
import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.common.widgets.DeejaydSelModel;
import org.mroy31.deejayd.webui.cellview.columns.GrippyCell;
import org.mroy31.deejayd.webui.cellview.columns.GrippyColumn;
import org.mroy31.deejayd.webui.client.WebuiLayout;
import org.mroy31.deejayd.webui.resources.WebuiResources;

import com.google.gwt.cell.client.ImageResourceCell;
import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.resources.client.ImageResource;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.uibinder.client.UiHandler;
import com.google.gwt.user.cellview.client.AbstractPager;
import com.google.gwt.user.cellview.client.Column;
import com.google.gwt.user.cellview.client.DeejaydCellTable;
import com.google.gwt.user.cellview.client.TextColumn;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.ScrollPanel;
import com.google.gwt.user.client.ui.Widget;
import com.google.gwt.view.client.ProvidesKey;
import com.google.gwt.view.client.RangeChangeEvent;

public class AudioLibView extends Composite implements LibraryChangeHandler {
    private WebuiLayout ui;

    private static AudioLibViewUiBinder uiBinder = GWT
            .create(AudioLibViewUiBinder.class);

    interface AudioLibViewUiBinder extends UiBinder<Widget, AudioLibView> {}

    @UiField(provided = true) DeejaydCellTable<LibraryItem> list;
    @UiField HorizontalPanel navBar;
    @UiField ScrollPanel listPanel;
    @UiField Button loadButton;
    @UiField Button loadQueueButton;
    @UiField CheckBox selectAll;
    @UiField(provided = true) final WebuiResources resources;

    private int PAGE_SIZE = 500;
    protected DeejaydSelModel<LibraryItem> selModel = new DeejaydSelModel<LibraryItem>();
    private LibraryProvider provider;


    public AudioLibView(final WebuiLayout ui) {
        this.ui = ui;
        this.resources = ui.resources;

        list = new DeejaydCellTable<LibraryItem>(PAGE_SIZE);
        list.setKeyProvider(new ProvidesKey<LibraryItem>() {

            public Object getKey(LibraryItem item) {
                return item.getPath();
            }
        });
        list.setRowCommand(new DeejaydCellTable.RowCommand<LibraryItem>() {

            public void execute(LibraryItem object) {
                setPath(object.getPath());
            }
        });
        list.addRangeChangeHandler(new RangeChangeEvent.Handler() {

            public void onRangeChange(RangeChangeEvent event) {
                listPanel.scrollToTop();
            }
        });

        provider = new LibraryProvider(ui, "audio");
        provider.addPathChangeHandler(new LibraryProvider.PathChangeHandler() {

            public void onPathChange(String path) {
                updateNavBar(path);
            }
        });
        provider.getDataProvider().addDataDisplay(list);
        list.setSelectionModel(selModel);

        initWidget(uiBinder.createAndBindUi(this));
        loadButton.setText(ui.i18nConstants.add());
        loadQueueButton.setText(ui.i18nConstants.addQueue());
        ui.audioLibrary.addLibraryChangeHandler(this);

        // add columns
        list.addColumn(new GrippyColumn<LibraryProvider.LibraryItem>("audiolib",
                list, ui.resources.webuiCss().grippyCell(),
                new GrippyCell.DragStartMessage() {

                    public String onDragStart(int count) {
                        return ui.i18nMessages.pathCount(count);
                    }
                }));
        list.setColumnWidth(0, "20px");

        list.addColumn(new Column<LibraryProvider.LibraryItem, ImageResource>(
                new ImageResourceCell()) {

            @Override
            public ImageResource getValue(LibraryItem object) {
                return object.getType().equals("file") ?
                        ui.resources.audio() : ui.resources.folder();
            }

        });
        list.setColumnWidth(1, "30px");

        list.addColumn(new TextColumn<LibraryProvider.LibraryItem>() {

            @Override
            public String getValue(LibraryItem object) {
                return object.getLabel();
            }
        });

        provider.onLibraryChange(null);
    }

    public void setPager(AbstractPager pager) {
        pager.setDisplay(list);
    }

    @UiHandler("loadButton")
    public void loadHandler(ClickEvent event) {
        ui.rpc.plsModeLoadPath(getSelection(), -1, new AnswerHandler<Boolean>() {

            public void onAnswer(Boolean answer) {
                ui.update();
                selModel.clearSelection();
                selectAll.setValue(false, false);
            }
        });
    }

    @UiHandler("loadQueueButton")
    public void loadQueueHandler(ClickEvent event) {
        ui.rpc.queueLoadPath(getSelection(), -1, new AnswerHandler<Boolean>() {

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

    public void onLibraryChange(LibraryChangeEvent event) {
        provider.onLibraryChange(event);
        // clear navBar
        navBar.clear();
    }

    private List<String> getSelection() {
        ArrayList<String> sel = new ArrayList<String>();
        if (selModel != null) {
            for (LibraryItem item : list.getDisplayedItems()) {
                if (selModel.isSelected(item))
                    sel.add(item.getPath());
            }
        }
        return sel;
    }

    private void setPath(String path) {
        provider.setPath(path);
    }

    private void updateNavBar(String path) {
        navBar.clear();
        if (path.equals(""))
            return;

        class navClickHandler implements ClickHandler {
            private int idx;
            private String[] rootPart;

            public navClickHandler(int idx, String[] rootPart) {
                this.idx = idx;
                this.rootPart = rootPart;
            }

            public void onClick(ClickEvent event) {
                String path = "";
                for (int j=0; j<idx+1 ; j++) {
                    if (path.equals("")) {
                        path = rootPart[j];
                    } else {
                        path += "/"+rootPart[j];
                    }
                }
                setPath(path);
            }
        }
        String[] rootPart = path.split("/");
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
}

//vim: ts=4 sw=4 expandtab