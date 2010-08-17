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

import java.util.ArrayList;
import java.util.HashMap;

import org.mroy31.deejayd.common.rpc.DefaultRpcCallback;
import org.mroy31.deejayd.common.rpc.GenericRpcCallback;
import org.mroy31.deejayd.mobile.client.MobileLayout;
import org.mroy31.deejayd.mobile.resources.MobileResources;
import org.mroy31.deejayd.mobile.widgets.ListPanel;
import org.mroy31.deejayd.mobile.widgets.LoadingWidget;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiFactory;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.Command;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.Widget;

public class VideoLibrary extends Composite implements ClickHandler {
    private final MobileLayout ui = MobileLayout.getInstance();
    private Command closeCommand;

    private static VideoLibraryUiBinder uiBinder = GWT
            .create(VideoLibraryUiBinder.class);
    interface VideoLibraryUiBinder extends UiBinder<Widget, VideoLibrary> {}

    private class Item extends Composite implements ClickHandler {
        private String path;

        public Item(String title, String p) {
            this.path = p;

            HorizontalPanel hPanel = makeHPanel();
            hPanel.setWidth("100%");
            hPanel.setSpacing(2);
            if (!title.equals("..")) {
                Label select = new Label(ui.i18nConst.select());
                select.addStyleName(ui.resources.mobileCss().button());
                select.addClickHandler(new ClickHandler() {
                    @Override
                    public void onClick(ClickEvent event) {
                        ui.rpc.videoModeSet(path, "directory",
                                new DefaultRpcCallback(ui));
                        closeCommand.execute();
                    }
                });
                hPanel.add(select);
            }

            hPanel.add(new Image(ui.resources.folder()));

            Label l = new Label(title);
            l.addClickHandler(this);
            hPanel.add(l);
            hPanel.setCellWidth(l, "100%");

            Image chevron = new Image(ui.resources.chevron());
            chevron.addClickHandler(this);
            hPanel.add(chevron);

            initWidget(hPanel);
        }

        public String getPath() {
            return path;
        }

        @Override
        public void onClick(ClickEvent event) {
            setDirectory(getPath());
        }
    }

    @UiField Label rootPath;
    @UiField HorizontalPanel pagerPanel;
    @UiField HorizontalPanel pager;
    @UiField Button goFirst;
    @UiField Button goPrevious;
    @UiField Button goNext;
    @UiField Button goLast;
    @UiField Label pageDesc;
    @UiField ListPanel list;
    @UiField(provided = true) final MobileResources resources = ui.resources;

    private ArrayList<HashMap<String, String>> dirList =
            new ArrayList<HashMap<String, String>>();
    private int currentPage;
    private int pageNumber;
    private int PAGE_SIZE = 20;

    public VideoLibrary(Command closeCmd) {
        this.closeCommand = closeCmd;
        initWidget(uiBinder.createAndBindUi(this));

        pagerPanel.setCellHorizontalAlignment(pager,
                HorizontalPanel.ALIGN_CENTER);
        for (Button btn : new Button[]{goFirst, goLast, goNext, goPrevious}) {
            btn.addClickHandler(this);
        }

        setDirectory("");
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

    public void setDirectory(final String rootDir) {
        dirList.clear();
        setLoading();

        rootPath.setText(rootDir);
        rootPath.setVisible(!rootDir.equals(""));
        ui.rpc.libGetDirectory("video", rootDir, new GenericRpcCallback() {
            @Override
            public void setError(String error) {
                ui.setError(error);
            }

            @Override
            public void onCorrectAnswer(JSONValue data) {
                JSONObject answer = data.isObject();

                if (!rootDir.equals("")) {
                    HashMap<String,String> root = new HashMap<String,String>();
                    root.put("title", "..");
                    root.put("path", getParentDir(rootDir));
                    dirList.add(root);
                }

                JSONArray dirs = answer.get("directories").isArray();
                for (int idx=0; idx<dirs.size(); idx++) {
                    HashMap<String,String> dAttrs = new HashMap<String,String>();
                    dAttrs.put("title", dirs.get(idx).isString().stringValue());
                    dAttrs.put("path", buildPath(rootDir,
                            dirs.get(idx).isString().stringValue()));
                    dirList.add(dAttrs);
                }

                currentPage = -1;
                pageNumber = (int) (dirList.size() / PAGE_SIZE);
                if ((dirList.size() % PAGE_SIZE) > 0)
                    pageNumber ++;
                pagerPanel.setVisible(pageNumber > 1);
                displayPage(1);
            }
        });
    }

    @Override
    public void onClick(ClickEvent event) {
        Widget source = (Widget) event.getSource();

        int page;
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
            list.clear();

            int start = (page-1)*PAGE_SIZE;
            int end = Math.min(dirList.size(), page*PAGE_SIZE);
            for (int idx=start; idx<end; idx++) {
                HashMap<String, String> item = dirList.get(idx);
                list.add(new Item(item.get("title"), item.get("path")));
            }

            currentPage = page;
            pageDesc.setText(Integer.toString(page)+"/"+
                    Integer.toString(pageNumber));
        }
    }

    private String buildPath(String root, String name) {
        return root.equals("") ? name : root+"/"+name;
    }

    private String getParentDir(String path) {
        String[] paths = path.split("/");
        if (paths.length > 1) {
            String ans = paths[0];
            for (int idx=1; idx<(paths.length-1); idx++)
                ans = ans+"/"+paths[idx];

            return ans;
        }
        return "";
    }
}

//vim: ts=4 sw=4 expandtab