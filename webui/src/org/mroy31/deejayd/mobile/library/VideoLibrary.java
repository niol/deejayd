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
import org.mroy31.deejayd.mobile.client.MobileLayout;
import org.mroy31.deejayd.mobile.resources.MobileResources;
import org.mroy31.deejayd.mobile.widgets.Pager;

import com.google.gwt.cell.client.AbstractCell;
import com.google.gwt.cell.client.ValueUpdater;
import com.google.gwt.core.client.GWT;
import com.google.gwt.dom.client.Element;
import com.google.gwt.dom.client.NativeEvent;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiFactory;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.cellview.client.Column;
import com.google.gwt.user.cellview.client.DeejaydCellTable;
import com.google.gwt.user.client.Command;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.Widget;

public class VideoLibrary extends AbstractLibrary {
    private final MobileLayout ui = MobileLayout.getInstance();
    private Command closeCommand;

    private static VideoLibraryUiBinder uiBinder = GWT
            .create(VideoLibraryUiBinder.class);
    interface VideoLibraryUiBinder extends UiBinder<Widget, VideoLibrary> {}

    @UiField Label rootPath;
    @UiField HorizontalPanel pagerPanel;
    @UiField(provided = true) Pager pager;
    @UiField(provided = true) DeejaydCellTable<LibraryProvider.LibraryItem> list;
    @UiField(provided = true) final MobileResources resources = ui.resources;

    public VideoLibrary(Command closeCmd) {
        super("video");

        list = getList();
        pager = new Pager();
        pager.setDisplay(list);
        this.closeCommand = closeCmd;

        initWidget(uiBinder.createAndBindUi(this));

        addColumns(list);
        provider.onLibraryChange(null);
    }

    @UiFactory
    HorizontalPanel makeHPanel() {
        HorizontalPanel panel = new HorizontalPanel();
        panel.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);

        return panel;
    }

    @Override
    void addFirstColumn(DeejaydCellTable<LibraryProvider.LibraryItem> l) {
        l.addColumn(new Column<LibraryProvider.LibraryItem, String>(
                new AbstractCell<String>("click") {

                    @Override
                    public void render(String value, Object key,
                            SafeHtmlBuilder sb) {
                        sb.appendHtmlConstant("<button class='");
                        sb.appendEscaped(ui.resources.mobileCss().button());
                        sb.appendHtmlConstant("'>");
                        sb.appendEscaped(ui.i18nConst.select());
                        sb.appendHtmlConstant("</button>");
                    }

                    @Override
                    public void onBrowserEvent(Element parent, String value,
                            Object key, NativeEvent event,
                            ValueUpdater<String> valueUpdater) {
                        ui.rpc.videoModeSet(value, "directory", null);
                        closeCommand.execute();
                    }
                }) {

                    @Override
                    public String getValue(LibraryItem object) {
                        return object.getPath();
                    }
        });
    }
}

//vim: ts=4 sw=4 expandtab