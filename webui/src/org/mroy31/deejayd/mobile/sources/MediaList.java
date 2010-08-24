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

package org.mroy31.deejayd.mobile.sources;

import org.mroy31.deejayd.common.rpc.GenericRpcCallback;
import org.mroy31.deejayd.mobile.client.MobileLayout;
import org.mroy31.deejayd.mobile.resources.MobileResources;
import org.mroy31.deejayd.mobile.widgets.ListPanel;
import org.mroy31.deejayd.mobile.widgets.LoadingWidget;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONNumber;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiFactory;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.Widget;

public class MediaList extends Composite implements ClickHandler {
    private final MobileLayout ui = MobileLayout.getInstance();

    private static MediaListUiBinder uiBinder = GWT
            .create(MediaListUiBinder.class);
    interface MediaListUiBinder extends UiBinder<Widget, MediaList> {}

    @UiField HorizontalPanel pagerPanel;
    @UiField HorizontalPanel pager;
    @UiField Button goFirst;
    @UiField Button goPrevious;
    @UiField Button goNext;
    @UiField Button goLast;
    @UiField Label pageDesc;
    @UiField ListPanel list;
    @UiField(provided = true) final MobileResources resources = ui.resources;

    private String source;
    private int currentPage;
    private int pageNumber;
    private int PAGE_SIZE = 15;
    private int length;
    private MediaListFormater formater;

    public MediaList(String source, MediaListFormater formater) {
        this.source = source;
        this.formater = formater;

        initWidget(uiBinder.createAndBindUi(this));
        pagerPanel.setCellHorizontalAlignment(pager,
                HorizontalPanel.ALIGN_CENTER);
        for (Button btn : new Button[]{goFirst, goLast, goNext, goPrevious}) {
            btn.addClickHandler(this);
        }
    }

    @UiFactory
    HorizontalPanel makeHPanel() {
        HorizontalPanel panel = new HorizontalPanel();
        panel.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);

        return panel;
    }

    public void setLoading() {
        list.clear();
        list.add(new LoadingWidget());
    }

    public void updateList(int length) {
        this.length = length;

        currentPage = -1;
        pageNumber = (int) (length / PAGE_SIZE);
        if ((length % PAGE_SIZE) > 0)
            pageNumber ++;
        pagerPanel.setVisible(pageNumber > 1);

        displayPage(1);
    }

    public void onClick(ClickEvent event) {
        int page;
        Widget source = (Widget) event.getSource();
        if (source == goFirst) {
            page = 1;
        } else if (source == goPrevious) {
            page = Math.max(currentPage - 1, 1);
        } else if (source == goNext) {
            page = Math.min(currentPage + 1, pageNumber);
        } else if (source == goLast) {
            page = pageNumber;
        } else {
            return;
        }
        displayPage(page);
    }

    private void displayPage(int page) {
        if (page != currentPage) {
            setLoading();

            int start = (page-1)*PAGE_SIZE;
            int l = Math.min(length, page*PAGE_SIZE);

            JSONArray args = new JSONArray();
            args.set(0, new JSONNumber(start));
            args.set(1, new JSONNumber(l));
            ui.rpc.send(source+".get", args, new GenericRpcCallback() {

                @Override
                public void setError(String error) {
                    ui.setError(error);
                }

                @Override
                public void onCorrectAnswer(JSONValue data) {
                    list.clear();
                    JSONArray jsList = data.isObject().get("medias").isArray();
                    for (int i = 0; i<jsList.size(); i++) {
                        list.add(formater.formatRow(jsList.get(i).isObject()));
                    }
                }
            });

            currentPage = page;
            pageDesc.setText(Integer.toString(page)+"/"+
                    Integer.toString(pageNumber));
        }
    }
}

//vim: ts=4 sw=4 expandtab