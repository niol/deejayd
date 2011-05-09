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

import org.mroy31.deejayd.common.events.DragLeaveEvent;
import org.mroy31.deejayd.common.events.DragLeaveHandler;
import org.mroy31.deejayd.common.events.DragOverEvent;
import org.mroy31.deejayd.common.events.DragOverHandler;
import org.mroy31.deejayd.common.events.DropEvent;
import org.mroy31.deejayd.common.events.DropHandler;
import org.mroy31.deejayd.common.events.StatusChangeEvent;
import org.mroy31.deejayd.common.events.StatusChangeHandler;
import org.mroy31.deejayd.common.provider.MediaListProvider;
import org.mroy31.deejayd.common.rpc.types.Media;
import org.mroy31.deejayd.common.widgets.DeejaydSelModel;
import org.mroy31.deejayd.webui.cellview.columns.CkSelColumn;
import org.mroy31.deejayd.webui.client.WebuiLayout;

import com.google.gwt.core.client.GWT;
import com.google.gwt.dom.client.Element;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.cellview.client.AbstractPager;
import com.google.gwt.user.cellview.client.Column;
import com.google.gwt.user.cellview.client.DeejaydCellTable;
import com.google.gwt.user.client.Command;
import com.google.gwt.user.client.Event;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.FlexTable;
import com.google.gwt.user.client.ui.Widget;
import com.google.gwt.view.client.ProvidesKey;
import com.google.gwt.view.client.Range;
import com.google.gwt.view.client.RangeChangeEvent;

public class AbstractMediaList extends Composite implements StatusChangeHandler {
    protected WebuiLayout ui;

    public static interface DnDCommand {

        public void onDragOver(int row);
        public void onDragLeave(int row);
        public void onDrop(DropEvent event, int row);

    }

    private class DragLeaveCommand extends Timer {
        private final Command cmd;

        public DragLeaveCommand(Command cmd) {
            this.cmd = cmd;
        }

        @Override
        public void run() {
            cmd.execute();
        }

    }
    private DragLeaveCommand dragLeaveScheduled;

    public static int DEFAULT_PAGE_SIZE = 50;

    private static NewMediaListUiBinder uiBinder = GWT
    .create(NewMediaListUiBinder.class);
    interface NewMediaListUiBinder extends UiBinder<Widget, AbstractMediaList> {}

    @UiField(provided = true) DeejaydCellTable<Media> mediaList;
    @UiField FlexTable header;
    @UiField ScrollMediaPanel mediaListPanel;

    protected DeejaydSelModel<Media> selModel;
    protected MediaListProvider provider;
    private int columnCount = 0;
    private int spanCount = 0;

    public AbstractMediaList(final WebuiLayout ui, final String source,
            int pageSize, Boolean hasSelection) {
        this.ui = ui;

        ProvidesKey<Media> keyProvider = new ProvidesKey<Media>() {

            public Object getKey(Media item) {
                // Always do a null check
                return (item == null) ? "" : item.getStrAttr("id")+"/"+item.getStrAttr("media_id");
            }
        };
        if (hasSelection)
            selModel = new DeejaydSelModel<Media>(keyProvider);
        mediaList = new DeejaydCellTable<Media>(pageSize, keyProvider);
        mediaList.addRangeChangeHandler(new RangeChangeEvent.Handler() {

            public void onRangeChange(RangeChangeEvent event) {
                mediaListPanel.scrollToTop();
            }
        });

        provider = new MediaListProvider(ui, source);
        provider.getDataProvider().addDataDisplay(mediaList);
        if (this.selModel != null) {
            mediaList.setSelectionModel(selModel);
        }
        initWidget(uiBinder.createAndBindUi(this));
    }

    public void onStatusChange(StatusChangeEvent event) {
        mediaList.clearRowStyle();
        provider.onStatusChange(event);
    }

    public void addDnDCommand(final DnDCommand cmd) {
        DropHandler dropHandler = new DropHandler() {
            public void onDrop(DropEvent event) {
                event.preventDefault();
                event.stopPropagation();

                int row = mediaList.findRow(Event.as(event.getNativeEvent()));
                cmd.onDrop(event, row);
            }
        };
        mediaList.addDropHandler(dropHandler);
        mediaListPanel.addDropHandler(dropHandler);

        DragOverHandler dragOverHandler = new DragOverHandler() {
            public void onDragOver(DragOverEvent event) {
                event.preventDefault();
                event.stopPropagation();

                int row = mediaList.findRow(Event.as(event.getNativeEvent()));
                if (dragLeaveScheduled != null) {
                    dragLeaveScheduled.cancel();
                    dragLeaveScheduled = null;
                }
                cmd.onDragOver(row);
            }
        };
        mediaList.addDragOverHandler(dragOverHandler);
        mediaListPanel.addDragOverHandler(dragOverHandler);

        DragLeaveHandler dragLeaveHandler = new DragLeaveHandler() {

            public void onDragLeave(DragLeaveEvent event) {
                event.preventDefault();
                event.stopPropagation();

                final int row = mediaList.findRow(Event.as(event.getNativeEvent()));
                dragLeaveScheduled = new DragLeaveCommand(new Command() {

                    public void execute() {
                        cmd.onDragLeave(row);
                    }
                });
                dragLeaveScheduled.schedule(100);
            }
        };
        mediaList.addDragLeaveHandler(dragLeaveHandler);
        mediaListPanel.addDragLeaveHandler(dragLeaveHandler);
    }

    public void addColumn(Column<Media, ?> column, Widget head) {
        addColumn(column, head, null, -1);
    }

    public void addColumn(Column<Media, ?> column, Widget head,
            String width) {
        addColumn(column, head, width, -1);
    }

    public void addColumn(Column<Media, ?> column, Widget head,
            int colspan) {
        addColumn(column, head, null, colspan);
    }

    public void addColumn(Column<Media, ?> column, Widget head,
            String width, int colspan) {
        mediaList.addColumn(column);
        header.setWidget(0, columnCount, head);
        if (width != null) {
            header.getColumnFormatter().setWidth(columnCount+spanCount, width);
            mediaList.setColumnWidth(columnCount+spanCount, width);
        }
        if (colspan != -1) {
            header.getFlexCellFormatter().setColSpan(0, columnCount, colspan);
            mediaList.setColumnSpan(columnCount, colspan);
            spanCount += colspan-1;
        }

        ++columnCount;
    }

    public DeejaydSelModel<Media> getSelectionModel() {
        return selModel;
    }

    public List<String> getSelection() {
        ArrayList<String> sel = new ArrayList<String>();
        if (selModel != null) {
            for (Media m : mediaList.getVisibleItems()) {
                if (selModel.isSelected(m))
                    sel.add(m.getStrAttr("id"));
            }
        }
        return sel;
    }

    public Element getRow(int row) {
        return mediaList.getRowElement(row);
    }

    public void setPager(AbstractPager pager) {
        pager.setDisplay(mediaList);
    }

    public void setPlaying(int row) {
        mediaList.setRowStyle(row, ui.resources.webuiCss().currentItem());
    }

    public void resetPlaying(int row) {
        mediaList.removeRowStyle(row);
    }

    public void scrollTo(final int row) {
        Range range = mediaList.getVisibleRange();
        if (row < range.getStart() || row >= range.getStart()+range.getLength()) {
            mediaList.setVisibleRange(Math.max(0, row-5), range.getLength());
        } else {
            try {
                ensureVisibleImpl(mediaListPanel.getElement(),
                        (Element) mediaList.getRowElement(row-range.getStart()));
            } catch (IndexOutOfBoundsException e) {}
        }
    }

    protected void addSelectionColumn() {
        if (selModel == null)
            return;

        // add a checkbox in the header to select/unselect all rows
        CheckBox allCk = new CheckBox();
        allCk.addValueChangeHandler(new ValueChangeHandler<Boolean>() {

            public void onValueChange(ValueChangeEvent<Boolean> event) {
                selModel.setSelected(mediaList.getVisibleItems(),
                        event.getValue());
            }
        });
        addColumn(new CkSelColumn<Media>(mediaList), allCk, "25px");
    }

    private native void ensureVisibleImpl(Element scroll, Element e) /*-{
        if (!e)
          return;

        var item = e;
        var realOffset = 0;
        while (item && (item != scroll)) {
          realOffset += item.offsetTop;
          item = item.offsetParent;
        }

        scroll.scrollTop = realOffset - scroll.offsetHeight / 2;
    }-*/;
}

//vim: ts=4 sw=4 expandtab