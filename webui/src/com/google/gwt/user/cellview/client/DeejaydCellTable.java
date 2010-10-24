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
package com.google.gwt.user.cellview.client;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.mroy31.deejayd.common.events.DragEnterEvent;
import org.mroy31.deejayd.common.events.DragEnterHandler;
import org.mroy31.deejayd.common.events.DragLeaveEvent;
import org.mroy31.deejayd.common.events.DragLeaveHandler;
import org.mroy31.deejayd.common.events.DragOverEvent;
import org.mroy31.deejayd.common.events.DragOverHandler;
import org.mroy31.deejayd.common.events.DropEvent;
import org.mroy31.deejayd.common.events.DropHandler;
import org.mroy31.deejayd.common.events.HasDropHandlers;

import com.google.gwt.cell.client.Cell;
import com.google.gwt.core.client.GWT;
import com.google.gwt.core.client.Scheduler;
import com.google.gwt.dom.client.Document;
import com.google.gwt.dom.client.Element;
import com.google.gwt.dom.client.EventTarget;
import com.google.gwt.dom.client.NodeList;
import com.google.gwt.dom.client.TableCellElement;
import com.google.gwt.dom.client.TableColElement;
import com.google.gwt.dom.client.TableElement;
import com.google.gwt.dom.client.TableRowElement;
import com.google.gwt.dom.client.TableSectionElement;
import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.resources.client.ClientBundle;
import com.google.gwt.resources.client.CssResource;
import com.google.gwt.resources.client.ImageResource;
import com.google.gwt.resources.client.ImageResource.ImageOptions;
import com.google.gwt.resources.client.ImageResource.RepeatStyle;
import com.google.gwt.safehtml.client.SafeHtmlTemplates;
import com.google.gwt.safehtml.shared.SafeHtml;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.cellview.client.HasDataPresenter.LoadingState;
import com.google.gwt.user.client.DOM;
import com.google.gwt.user.client.Event;
import com.google.gwt.view.client.ProvidesKey;
import com.google.gwt.view.client.Range;
import com.google.gwt.view.client.SelectionModel;

/**
 * A list view that supports paging and columns.
 *
 * @param <T> the data type of each row
 */
public class DeejaydCellTable<T> extends AbstractHasData<T> implements HasDropHandlers {

    /**
     * A ClientBundle that provides images for this widget.
     */
    public static interface Resources extends ClientBundle {
        /**
         * The loading indicator used while the table is waiting for data.
         */
        ImageResource cellTableLoading();

        /**
         * The background used for selected cells.
         */
        @Source("cellListSelectedBackground.png")
        @ImageOptions(repeatStyle = RepeatStyle.Horizontal)
        ImageResource cellTableSelectedBackground();

        /**
         * The styles used in this widget.
         */
        @Source("DeejaydCellTable.css")
        Style cellTableStyle();
    }

    /**
     * Styles used by this widget.
     */
    public static interface Style extends CssResource {

        /**
         * Applied to every cell.
         */
        String cell();

        /**
         * Applied to the table.
         */
        String cellTable();

        /**
         * Applied to even rows.
         */
        String evenRow();

        /**
         * Applied to the loading indicator.
         */
        String loading();

        /**
         * Applied to odd rows.
         */
        String oddRow();

        /**
         * Applied to selected rows.
         */
        String selectedRow();
    }

    interface Template extends SafeHtmlTemplates {
        @Template("<div class=\"{0}\"/>")
        SafeHtml loading(String loading);

        @Template("<table><tbody>{0}</tbody></table>")
        SafeHtml tbody(SafeHtml rowHtml);

        @Template("<td class=\"{0}\"><div style=\"outline:none;\">{1}</div></td>")
        SafeHtml td(String classes, SafeHtml contents);

        @Template("<td class=\"{0}\" colspan=\"{1}\"><div style=\"outline:none;\">{2}</div></td>")
        SafeHtml tdWithColSpan(String classes, int colspan, SafeHtml contents);

        @Template("<tr onclick=\"\" class=\"{0}\">{1}</tr>")
        SafeHtml tr(String classes, SafeHtml contents);
    }

    /**
     * Implementation of {@link DeejaydCellTable}.
     */
    private static class Impl {

        private final com.google.gwt.user.client.Element tmpElem =
            Document.get().createDivElement().cast();

        /**
         * Convert the rowHtml into Elements wrapped by the specified table section.
         *
         * @param table the {@link DeejaydCellTable}
         * @param sectionTag the table section tag
         * @param rowHtml the Html for the rows
         * @return the section element
         */
        protected TableSectionElement convertToSectionElement(
                DeejaydCellTable<?> table, String sectionTag, SafeHtml rowHtml) {
            // Attach an event listener so we can catch synchronous load events from
            // cached images.
            DOM.setEventListener(tmpElem, table);

            // Render the rows into a table.
            // IE doesn't support innerHtml on a TableSection or Table element, so we
            // generate the entire table.
            sectionTag = sectionTag.toLowerCase();
            if ("tbody".equals(sectionTag)) {
                tmpElem.setInnerHTML(template.tbody(rowHtml).asString());
            } else {
                throw new IllegalArgumentException("Invalid table section tag: "
                        + sectionTag);
            }
            TableElement tableElem = tmpElem.getFirstChildElement().cast();

            // Detach the event listener.
            DOM.setEventListener(tmpElem, null);

            // Get the section out of the table.
            if ("tbody".equals(sectionTag)) {
                return tableElem.getTBodies().getItem(0);
            }
            throw new IllegalArgumentException(
                    "Invalid table section tag: " + sectionTag);
        }

        /**
         * Render a table section in the table.
         *
         * @param table the {@link DeejaydCellTable}
         * @param section the {@link TableSectionElement} to replace
         * @param html the html to render
         */
        protected void replaceAllRows(DeejaydCellTable<?> table,
                TableSectionElement section, SafeHtml html) {
            // If the widget is not attached, attach an event listener so we can catch
            // synchronous load events from cached images.
            if (!table.isAttached()) {
                DOM.setEventListener(table.getElement(), table);
            }

            // Render the html.
            section.setInnerHTML(html.asString());

            // Detach the event listener.
            if (!table.isAttached()) {
                DOM.setEventListener(table.getElement(), null);
            }
        }
    }

    /**
     * The default page size.
     */
    private static final int DEFAULT_PAGESIZE = 100;

    private static Template template;

    private static Resources DEFAULT_RESOURCES;

    /**
     * The table specific {@link Impl}.
     */
    private static Impl TABLE_IMPL;

    private static Resources getDefaultResources() {
        if (DEFAULT_RESOURCES == null) {
            DEFAULT_RESOURCES = GWT.create(Resources.class);
        }
        return DEFAULT_RESOURCES;
    }

    private boolean dependsOnSelection;
    private boolean handlesSelection;

    private boolean cellIsEditing;
    private final TableColElement colgroup;
    private final HashMap<Integer, String> rowStyles =
        new HashMap<Integer, String>();

    private final List<Column<T, ?>> columns = new ArrayList<Column<T, ?>>();
    private final HashMap<Integer, Integer> columnsSpan =
        new HashMap<Integer, Integer>();

    /**
     * Indicates whether or not the scheduled redraw has been cancelled.
     */
    private boolean redrawCancelled;

    /**
     * The command used to redraw the table after adding columns.
     */
    private final Scheduler.ScheduledCommand redrawCommand =
        new Scheduler.ScheduledCommand() {
        public void execute() {
            redrawScheduled = false;
            if (redrawCancelled) {
                redrawCancelled = false;
                return;
            }
            redraw();
        }
    };

    /**
     * Indicates whether or not a redraw is scheduled.
     */
    private boolean redrawScheduled;

    private final Style style;
    private final TableElement table;
    private final TableSectionElement tbody;
    private final TableSectionElement tbodyLoading;

    /**
     * Constructs a table with a default page size of 15.
     */
    public DeejaydCellTable() {
        this(DEFAULT_PAGESIZE);
    }

    /**
     * Constructs a table with the given page size.
     *
     * @param pageSize the page size
     */
    public DeejaydCellTable(final int pageSize) {
        this(pageSize, getDefaultResources());
    }

    /**
     * Constructs a table with the given page size.
     *
     * @param pageSize the page size
     * @param resources the resources to use for this widget
     */
    public DeejaydCellTable(final int pageSize, Resources resources) {
        this(pageSize, resources, null);
    }

    /**
     * Constructs a table with the given page size with the specified
     * {@link Resources}.
     *
     * @param pageSize the page size
     * @param keyProvider an instance of ProvidesKey<T>, or null if the record
     *          object should act as its own key
     */
    public DeejaydCellTable(final int pageSize, ProvidesKey<T> keyProvider) {
        this(pageSize, getDefaultResources(), keyProvider);
    }

    /**
     * Constructs a table with the given page size with the specified
     * {@link Resources}.
     *
     * @param pageSize the page size
     * @param resources the resources to use for this widget
     * @param keyProvider an instance of ProvidesKey<T>, or null if the record
     *          object should act as its own key
     */
    public DeejaydCellTable(final int pageSize, Resources resources,
            ProvidesKey<T> keyProvider) {
        super(Document.get().createTableElement(), pageSize, keyProvider);

        if (TABLE_IMPL == null) {
            TABLE_IMPL = GWT.create(Impl.class);
        }
        if (template == null) {
            template = GWT.create(Template.class);
        }
        this.style = resources.cellTableStyle();
        this.style.ensureInjected();

        table = getElement().cast();
        table.setCellSpacing(0);
        colgroup = Document.get().createColGroupElement();
        table.appendChild(colgroup);
        table.appendChild(tbody = Document.get().createTBodyElement());
        table.appendChild(tbodyLoading = Document.get().createTBodyElement());
        setStyleName(this.style.cellTable());

        // Create the loading indicator.
        {
            TableCellElement td = Document.get().createTDElement();
            TableRowElement tr = Document.get().createTRElement();
            tbodyLoading.appendChild(tr);
            tr.appendChild(td);
            td.setAlign("center");
            td.setInnerHTML("<div class='" + style.loading() + "'></div>");
            setLoadingIconVisible(false);
        }

        // Sink events.
        Set<String> eventTypes = new HashSet<String>();
        CellBasedWidgetImpl.get().sinkEvents(this, eventTypes);
    }

    /**
     * Sets the object used to determine how a row is styled; the change will take
     * effect the next time that the table is rendered.
     */
    public void setRowStyle(int row, String style) {
        rowStyles.put(row, style);
        Range range = getVisibleRange();
        if (row >= range.getStart() && row < range.getStart()+range.getLength()) {
             try {
                 getRowElement(row-range.getStart()).addClassName(style);
             } catch (IndexOutOfBoundsException e) {
                 return;
             }
        }
    }

    public void removeRowStyle(int row) {
        if (rowStyles.containsKey(row)) {
            Range rg = getVisibleRange();
            if (row >= rg.getStart() && row < rg.getStart()+rg.getLength()) {
                try {
                    getRowElement(row-rg.getStart())
                        .removeClassName(rowStyles.get(row));
                } catch (IndexOutOfBoundsException e) {}
            }
            rowStyles.remove(row);
        }
    }

    public void clearRowStyle() {
        rowStyles.clear();
    }

    /**
     * Adds a column to the table
     */
     public void addColumn(Column<T, ?> col) {
        columns.add(col);
        updateDependsOnSelection();

        // Sink events used by the new column.
        Set<String> consumedEvents = new HashSet<String>();
        {
            Set<String> cellEvents = col.getCell().getConsumedEvents();
            if (cellEvents != null) {
                consumedEvents.addAll(cellEvents);
            }
        }
        CellBasedWidgetImpl.get().sinkEvents(this, consumedEvents);

        scheduleRedraw();
     }

     /**
      * Add a style name to the {@link TableColElement} at the specified index,
      * creating it if necessary.
      *
      * @param index the column index
      * @param styleName the style name to add
      */
     public void addColumnStyleName(int index, String styleName) {
         ensureTableColElement(index).addClassName(styleName);
     }

     /**
      * Set width to the {@link TableColElement} at the specified index,
      * creating it if necessary.
      *
      * @param index the column index
      * @param width width of the column
      */
     public void setColumnWidth(int index, String width) {
         ensureTableColElement(index).setWidth(width);
     }

     /**
      * Set colspan to the {@link TableColElement} at the specified index,
      * creating it if necessary.
      *
      * @param index the column index
      * @param span colspan of the column
      */
     public void setColumnSpan(int index, int span) {
         columnsSpan.put(index, span);
         scheduleRedraw();
     }

     public int getHeight() {
         int height = getClientHeight(tbody);
         return height;
     }

     /**
      * Get the {@link TableRowElement} for the specified row. If the row element
      * has not been created, null is returned.
      *
      * @param row the row index
      * @return the row element, or null if it doesn't exists
      * @throws IndexOutOfBoundsException if the row index is outside of the
      *           current page
      */
     public TableRowElement getRowElement(int row) {
         checkRowBounds(row);
         NodeList<TableRowElement> rows = tbody.getRows();
         return rows.getLength() > row ? rows.getItem(row) : null;
     }

     @Override
     public void onBrowserEvent2(Event event) {
         String eventType = event.getType();

         // Find the cell where the event occurred.
         EventTarget eventTarget = event.getEventTarget();
         TableCellElement tableCell = null;
         if (eventTarget != null && Element.is(eventTarget)) {
             tableCell = findNearestParentCell(Element.as(eventTarget));
         }
         if (tableCell == null) {
             return;
         }

         Element trElem = tableCell.getParentElement();
         if (trElem == null) {
             return;
         }
         TableRowElement tr = TableRowElement.as(trElem);

         // Forward the event to the column.
         int col = tableCell.getCellIndex();
         int row = tr.getSectionRowIndex();

         T value = getDisplayedItem(row);
         fireEventToCell(event, eventType, tableCell, value, col, row);
     }

     public int findRow(Event event) {
         // Find the cell where the event occurred.
         EventTarget eventTarget = event.getEventTarget();
         TableCellElement tableCell = null;
         if (eventTarget != null && Element.is(eventTarget)) {
             tableCell = findNearestParentCell(Element.as(eventTarget));
         }
         if (tableCell == null) {
             return -1;
         }

         Element trElem = tableCell.getParentElement();
         if (trElem == null) {
             return -1;
         }
         TableRowElement tr = TableRowElement.as(trElem);
         return tr.getSectionRowIndex();
     }

     public HandlerRegistration addDragEnterHandler(DragEnterHandler handler) {
         return addDomHandler(handler, DragEnterEvent.getType());
     }

     public HandlerRegistration addDragLeaveHandler(DragLeaveHandler handler) {
         return addDomHandler(handler, DragLeaveEvent.getType());
     }

     public HandlerRegistration addDragOverHandler(DragOverHandler handler) {
         return addDomHandler(handler, DragOverEvent.getType());
     }

     public HandlerRegistration addDropHandler(DropHandler handler) {
         return addDomHandler(handler, DropEvent.getType());
     }

     /**
      * Remove a column.
      *
      * @param col the column to remove
      */
     public void removeColumn(Column<T, ?> col) {
         int index = columns.indexOf(col);
         if (index < 0) {
             throw new IllegalArgumentException(
                     "The specified column is not part of this table.");
         }
         removeColumn(index);
     }

     /**
      * Remove a column.
      *
      * @param index the column index
      */
     public void removeColumn(int index) {
         if (index < 0 || index >= columns.size()) {
             throw new IndexOutOfBoundsException(
                     "The specified column index is out of bounds.");
         }
         columns.remove(index);
         updateDependsOnSelection();
         scheduleRedraw();

         // We don't unsink events because other handlers or user code may have sunk
         // them intentionally.
     }

     /**
      * Remove a style from the {@link TableColElement} at the specified index.
      *
      * @param index the column index
      * @param styleName the style name to remove
      */
     public void removeColumnStyleName(int index, String styleName) {
         if (index >= colgroup.getChildCount()) {
             return;
         }
         ensureTableColElement(index).removeClassName(styleName);
     }

     @Override
     public void setSelected(Element elem, boolean selected) {
         setStyleName(elem, style.selectedRow(), selected);
     }

     @Override
     protected void renderRowValues(SafeHtmlBuilder sb, List<T> values, int start,
             SelectionModel<? super T> selectionModel) {

         ProvidesKey<T> keyProvider = getKeyProvider();
         String evenRowStyle = style.evenRow();
         String oddRowStyle = style.oddRow();
         String cellStyle = style.cell();
         String selectedRowStyle = " " + style.selectedRow();
         int length = values.size();
         int end = start + length;
         for (int i = start; i < end; i++) {
             T value = values.get(i - start);
             boolean isSelected = (selectionModel == null || value == null)
                     ? false : selectionModel.isSelected(value);
             boolean isEven = i % 2 == 0;
             String trClasses = isEven ? evenRowStyle : oddRowStyle;
             if (isSelected) {
               trClasses += selectedRowStyle;
             }

             if (rowStyles.containsKey(i)) {
                 trClasses += " "+rowStyles.get(i);
             }

             SafeHtmlBuilder trBuilder = new SafeHtmlBuilder();
             int curColumn = 0;
             for (Column<T, ?> column : columns) {
                 SafeHtmlBuilder cellBuilder = new SafeHtmlBuilder();
                 if (value != null) {
                   column.render(value, keyProvider, cellBuilder);
                 }

                 if (columnsSpan.containsKey(curColumn)) {
                     trBuilder.append(template.tdWithColSpan(cellStyle,
                             columnsSpan.get(curColumn),
                             cellBuilder.toSafeHtml()));
                 } else {
                     trBuilder.append(template.td(cellStyle,
                             cellBuilder.toSafeHtml()));
                 }

                 curColumn++;
             }

             sb.append(template.tr(trClasses, trBuilder.toSafeHtml()));
         }
     }

     @Override
     protected Element convertToElements(SafeHtml html) {
         return TABLE_IMPL.convertToSectionElement(DeejaydCellTable.this, "tbody", html);
     }

     @Override
     protected boolean dependsOnSelection() {
         return dependsOnSelection;
     }

     @Override
     protected Element getChildContainer() {
         return tbody;
     }

     @Override
     protected void onUpdateSelection() {
     }

     @Override
     protected void replaceAllChildren(List<T> values, SafeHtml html) {
         // Cancel any pending redraw.
         if (redrawScheduled) {
             redrawCancelled = true;
         }
         TABLE_IMPL.replaceAllRows(DeejaydCellTable.this, tbody,
                    CellBasedWidgetImpl.get().processHtml(html));
     }

     @Override
     protected void setLoadingState(LoadingState state) {
         setLoadingIconVisible(state == LoadingState.LOADING);
     }

     @Override
     protected Element getKeyboardSelectedElement() {
         return null;
     }

     @Override
     protected boolean isKeyboardNavigationSuppressed() {
         return true;
     }

     @Override
     protected boolean resetFocusOnCell() {
         return false;
     }

     @Override
     protected void setKeyboardSelected(int index, boolean selected,
             boolean stealFocus) {
     }
     /**
      * Get the {@link TableColElement} at the specified index, creating it if
      * necessary.
      *
      * @param index the column index
      * @return the {@link TableColElement}
      */
     private TableColElement ensureTableColElement(int index) {
         // Ensure that we have enough columns.
         for (int i = colgroup.getChildCount(); i <= index; i++) {
             colgroup.appendChild(Document.get().createColElement());
         }
         return colgroup.getChild(index).cast();
     }

     /**
      * Find the cell that contains the element. Note that the TD element is not
      * the parent. The parent is the div inside the TD cell.
      *
      * @param elem the element
      * @return the parent cell
      */
     private TableCellElement findNearestParentCell(Element elem) {
         while ((elem != null) && (elem != table)) {
             // TODO: We need is() implementations in all Element subclasses.
             // This would allow us to use TableCellElement.is() -- much cleaner.
             String tagName = elem.getTagName();
             if ("td".equalsIgnoreCase(tagName) || "th".equalsIgnoreCase(tagName)) {
                 return elem.cast();
             }
             elem = elem.getParentElement();
         }
         return null;
     }

     /**
      * Fire an event to the Cell within the specified {@link TableCellElement}.
      */
     @SuppressWarnings("unchecked")
     private <C> void fireEventToCell(Event event, String eventType,
             TableCellElement tableCell, T value, int col, int row) {
         Column<T, C> column = (Column<T, C>) columns.get(col);
         Cell<C> cell = column.getCell();
         if (cellConsumesEventType(cell, eventType)) {
             C cellValue = column.getValue(value);
             ProvidesKey<T> providesKey = getKeyProvider();
             Object key = providesKey == null ? value : providesKey.getKey(value);
             Element parentElem = tableCell.getFirstChildElement();
             boolean cellWasEditing = cell.isEditing(parentElem, cellValue, key);
             column.onBrowserEvent(
                     parentElem, getPageStart() + row, value, event, providesKey);
             cellIsEditing = cell.isEditing(parentElem, cellValue, key);
             if (cellWasEditing && !cellIsEditing) {
                 resetFocusOnCell();
             }
         }
     }

     private native int getClientHeight(Element element) /*-{
    return element.clientHeight;
  }-*/;

     /**
      * Schedule a redraw for the end of the event loop.
      */
     private void scheduleRedraw() {
         redrawCancelled = false;
         if (!redrawScheduled) {
             redrawScheduled = true;
             Scheduler.get().scheduleFinally(redrawCommand);
         }
     }

     /**
      * Show or hide the loading icon.
      *
      * @param visible true to show, false to hide.
      */
     private void setLoadingIconVisible(boolean visible) {
         // Clear the current data.
         if (visible) {
             tbody.setInnerText("");
         }

         // Update the colspan.
         TableCellElement td = tbodyLoading.getRows().getItem(0)
         .getCells().getItem(0);
         td.setColSpan(Math.max(1, columns.size()));
         setVisible(tbodyLoading, visible);
     }

     /**
      * Update the dependsOnSelection and handlesSelection booleans.
      */
     private void updateDependsOnSelection() {
         dependsOnSelection = false;
         handlesSelection = false;
         for (Column<T, ?> column : columns) {
             Cell<?> cell = column.getCell();
             if (cell.dependsOnSelection()) {
                 dependsOnSelection = true;
             }
             if (cell.handlesSelection()) {
                 handlesSelection = true;
             }
         }
     }
}

//vim: ts=4 sw=4 expandtab