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

package org.mroy31.deejayd.mobile.library;

import java.util.ArrayList;

import org.mroy31.deejayd.common.provider.LibraryProvider;
import org.mroy31.deejayd.common.provider.LibraryProvider.LibraryItem;
import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.mobile.resources.MobileResources;
import org.mroy31.deejayd.mobile.widgets.Pager;

import com.google.gwt.cell.client.FieldUpdater;
import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiFactory;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.uibinder.client.UiHandler;
import com.google.gwt.user.cellview.client.Column;
import com.google.gwt.user.cellview.client.DeejaydCellTable;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.Widget;

public class AudioLibrary extends AbstractLibrary {

    private static AudioLibraryUiBinder uiBinder = GWT
            .create(AudioLibraryUiBinder.class);
    interface AudioLibraryUiBinder extends UiBinder<Widget, AudioLibrary> { }

    @UiField Label rootPath;
    @UiField(provided = true) Pager pager;
    @UiField(provided = true) DeejaydCellTable<LibraryProvider.LibraryItem> list;
    @UiField Label loadButton;
    @UiField(provided = true) final MobileResources resources = ui.resources;

    public AudioLibrary() {
        super("audio");

        list = getList();
        pager = new Pager();
        pager.setDisplay(list);

        initWidget(uiBinder.createAndBindUi(this));
        loadButton.setText(ui.i18nConst.add());

        addColumns(list);
        provider.onLibraryChange(null);
    }

    @UiFactory
    HorizontalPanel makeHPanel() {
        HorizontalPanel panel = new HorizontalPanel();
        panel.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);

        return panel;
    }


    @UiHandler("loadButton")
    public void loadButtonHandler(ClickEvent event) {
            ArrayList<String> selection = new ArrayList<String>();
            for (LibraryProvider.LibraryItem item : selModel.getSelectedSet()) {
                selection.add(item.getPath());
            }

            if (selection.size() > 0) {
                ui.rpc.plsModeLoadPath(selection, -1,
                        new AnswerHandler<Boolean>() {

                            public void onAnswer(Boolean answer) {
                                selModel.setSelected(list.getDisplayedItems(),
                                        false);
                                ui.setMessage(ui.i18nConst.plsAddMsg());
                                ui.update();
                            }
                        });
            }
    }

    @Override
    void addFirstColumn(DeejaydCellTable<LibraryProvider.LibraryItem> l) {
        Column<LibraryProvider.LibraryItem, Boolean> selColumn =
            new Column<LibraryProvider.LibraryItem, Boolean>(new SelCell()) {

            @Override
            public Boolean getValue(LibraryItem object) {
                return selModel.isSelected(object);
            }
        };
        selColumn.setFieldUpdater(new FieldUpdater<LibraryProvider.LibraryItem,
                Boolean>() {

            public void update(int index, LibraryProvider.LibraryItem object,
                    Boolean value) {
                selModel.setSelected(object, value);
            }
        });
        l.addColumn(selColumn);
    }
}

//vim: ts=4 sw=4 expandtab