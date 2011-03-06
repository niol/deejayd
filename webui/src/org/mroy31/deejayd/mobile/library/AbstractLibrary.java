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

import org.mroy31.deejayd.common.provider.LibraryProvider;
import org.mroy31.deejayd.common.provider.LibraryProvider.LibraryItem;
import org.mroy31.deejayd.common.widgets.DeejaydSelModel;
import org.mroy31.deejayd.mobile.client.MobileLayout;

import com.google.gwt.cell.client.AbstractCell;
import com.google.gwt.cell.client.CheckboxCell;
import com.google.gwt.cell.client.ImageResourceCell;
import com.google.gwt.cell.client.ValueUpdater;
import com.google.gwt.dom.client.Element;
import com.google.gwt.dom.client.NativeEvent;
import com.google.gwt.resources.client.ImageResource;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.cellview.client.Column;
import com.google.gwt.user.cellview.client.DeejaydCellTable;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.AbstractImagePrototype;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.view.client.RangeChangeEvent;

abstract class AbstractLibrary extends Composite {
    final MobileLayout ui = MobileLayout.getInstance();

    DeejaydSelModel<LibraryProvider.LibraryItem> selModel =
            new DeejaydSelModel<LibraryProvider.LibraryItem>(null);
    LibraryProvider provider;
    int PAGE_SIZE = 20;

    class SelCell extends CheckboxCell {

        public SelCell() {
            super(true, true);
        }

        @Override
        public boolean handlesSelection() {
            return false;
        }
    }

    public AbstractLibrary(String type) {
        provider = new LibraryProvider(ui, type, true);
    }

    protected DeejaydCellTable<LibraryProvider.LibraryItem> getList() {
        DeejaydCellTable<LibraryProvider.LibraryItem> l =
            new DeejaydCellTable<LibraryProvider.LibraryItem>(PAGE_SIZE,
                ui.resources);
        l.addRangeChangeHandler(new RangeChangeEvent.Handler() {

            public void onRangeChange(RangeChangeEvent event) {
                Window.scrollTo(0, 0);
            }
        });
        provider.getDataProvider().addDataDisplay(l);
        l.setSelectionModel(selModel);

        return l;
    }

    protected void addColumns(DeejaydCellTable<LibraryProvider.LibraryItem> l) {
        addFirstColumn(l);

        l.addColumn(new Column<LibraryProvider.LibraryItem, ImageResource>(
                new ImageResourceCell()) {

                    @Override
                    public ImageResource getValue(LibraryItem object) {
                        if (object.getType().equals("directory"))
                            return ui.resources.folder();
                        else
                            return ui.resources.audioFile();
                    }

        });

        l.addColumn(new Column<LibraryProvider.LibraryItem, String>(
                new AbstractCell<String>("click") {

                    @Override
                    public void onBrowserEvent(Context ctx, Element parent,
                            String value, NativeEvent event,
                            ValueUpdater<String> valueUpdater) {
                        String path = ((LibraryProvider.LibraryItem) ctx.getKey())
                                .getPath();
                        provider.setPath(path);
                    }

                    @Override
                    public void render(Context context, String value,
                            SafeHtmlBuilder sb) {
                        if (value != null) {
                            sb.appendEscaped(value);

                      }
                    }
                }) {

                    @Override
                    public String getValue(LibraryItem object) {
                        return object.getLabel();
                    }

        });
        l.setColumnWidth(2, "100%");

        l.addColumn(new Column<LibraryProvider.LibraryItem, ImageResource>(
                new AbstractCell<ImageResource>("click") {

                    @Override
                    public void onBrowserEvent(Context ctx, Element parent,
                            ImageResource value, NativeEvent event,
                            ValueUpdater<ImageResource> valueUpdater) {
                        String path = ((LibraryProvider.LibraryItem) ctx.getKey())
                                .getPath();
                        provider.setPath(path);
                    }

                    @Override
                    public void render(Context context, ImageResource value,
                            SafeHtmlBuilder sb) {
                        if (value != null) {
                            sb.appendHtmlConstant(AbstractImagePrototype
                                    .create(value).getHTML());
                      }
                    }
                }) {

                    @Override
                    public ImageResource getValue(LibraryItem object) {
                        return ui.resources.chevron();
                    }

        });
    }

    abstract void addFirstColumn(DeejaydCellTable<LibraryProvider.LibraryItem> l);
}

//vim: ts=4 sw=4 expandtab