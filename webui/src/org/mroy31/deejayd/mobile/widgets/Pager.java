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

package org.mroy31.deejayd.mobile.widgets;

import org.mroy31.deejayd.mobile.client.MobileLayout;
import org.mroy31.deejayd.mobile.resources.MobileResources;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.uibinder.client.UiHandler;
import com.google.gwt.user.cellview.client.AbstractPager;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.Widget;

public class Pager extends AbstractPager {
    private final MobileLayout ui = MobileLayout.getInstance();

    private static MediaListUiBinder uiBinder = GWT
            .create(MediaListUiBinder.class);
    interface MediaListUiBinder extends UiBinder<Widget, Pager> {}

    @UiField Label pageDesc;
    @UiField(provided = true) final MobileResources resources = ui.resources;

    public Pager() {
        initWidget(uiBinder.createAndBindUi(this));
    }

    @UiHandler("goFirst")
    public void goFirstHandler(ClickEvent event) {
        firstPage();
    }

    @UiHandler("goPrevious")
    public void goPreviousHandler(ClickEvent event) {
        previousPage();
    }

    @UiHandler("goNext")
    public void goNextHandler(ClickEvent event) {
        nextPage();
    }

    @UiHandler("goLast")
    public void goLastHandler(ClickEvent event) {
        lastPage();
    }

    @Override
    protected void onRangeOrRowCountChanged() {
        setVisible(getPageCount() > 1);
        pageDesc.setText(Integer.toString(getPage()+1)+"/"+
                Integer.toString(getPageCount()));
    }
}

//vim: ts=4 sw=4 expandtab