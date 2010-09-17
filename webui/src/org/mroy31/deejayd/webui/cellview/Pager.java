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

import org.mroy31.deejayd.webui.client.WebuiLayout;
import org.mroy31.deejayd.webui.resources.WebuiResources;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.uibinder.client.UiHandler;
import com.google.gwt.user.cellview.client.AbstractPager;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.Widget;

public class Pager extends AbstractPager {

    private static PagerUiBinder uiBinder = GWT.create(PagerUiBinder.class);
    interface PagerUiBinder extends UiBinder<Widget, Pager> {}

    @UiField Label pageDesc;
    @UiField(provided = true) final WebuiResources resources;

    public Pager(WebuiLayout ui) {
        resources = ui.resources;
        initWidget(uiBinder.createAndBindUi(this));
    }

    @UiHandler("goFirst")
    public void goFirstHandler(ClickEvent event) {
        firstPage();
    }

    @UiHandler("goPrevious")
    public void goPreviousHandler(ClickEvent event) {
        if (hasPreviousPage())
            previousPage();
    }

    @UiHandler("goNext")
    public void goNextHandler(ClickEvent event) {
        if (hasNextPage())
            nextPage();
    }

    @UiHandler("goLast")
    public void goLastHandler(ClickEvent event) {
        lastPage();
    }

    @Override
    protected void onRangeOrRowCountChanged() {
        setVisible(getPageCount() > 1);
        int end = Math.min(getDisplay().getRowCount(),
                getPageStart()+getPageSize());
        pageDesc.setText(Integer.toString(getPageStart())+"-"
                +Integer.toString(end)+" / "
                +Integer.toString(getDisplay().getRowCount()));
    }
}

//vim: ts=4 sw=4 expandtab