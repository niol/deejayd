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

package org.mroy31.deejayd.common.provider;

import java.util.ArrayList;

import org.mroy31.deejayd.common.events.LibraryChangeEvent;
import org.mroy31.deejayd.common.events.LibraryChangeHandler;
import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.common.rpc.types.FileDirList;
import org.mroy31.deejayd.common.rpc.types.Media;
import org.mroy31.deejayd.common.widgets.DeejaydUIWidget;

import com.google.gwt.view.client.AsyncDataProvider;
import com.google.gwt.view.client.HasData;
import com.google.gwt.view.client.Range;

public class LibraryProvider implements LibraryChangeHandler {
    private final DeejaydUIWidget ui;
    private final String libType;
    private final boolean withParentItem;

    public static interface PathChangeHandler {
        public void onPathChange(String path);
    }
    private ArrayList<PathChangeHandler> handlers =
        new ArrayList<PathChangeHandler>();

    public static class LibraryItem {
        private String path;
        private String type;
        private String label;

        public LibraryItem(String root, String dir) {
            this(root, dir, dir);
        }

        public LibraryItem(String root, String dir, String label) {
            this.type = "directory";
            this.path = root.equals("") ? dir : root + "/" + dir;
            this.label = label;
        }

        public LibraryItem(String root, Media m) {
            this.type = "file";
            this.path = root.equals("") ? m.getStrAttr("filename") :
                root + "/" + m.getStrAttr("filename");
            this.label = m.getStrAttr("filename");
        }

        public String getLabel() {
            return label;
        }

        public String getPath() {
            return path;
        }

        public String getType() {
            return type;
        }
    }

    private String currentPath = "";
    private ArrayList<LibraryItem> currentList = new ArrayList<LibraryItem>();
    private AsyncDataProvider<LibraryItem> dataProvider=new AsyncDataProvider<LibraryItem>() {

        @Override
        protected void onRangeChanged(HasData<LibraryItem> display) {
            Range rg = display.getVisibleRange();
            if (currentList.size() > rg.getStart()) {
                int toIdx = Math.min(currentList.size()-1,
                        rg.getStart()+rg.getLength());
                dataProvider.updateRowData(rg.getStart(),
                        currentList.subList(rg.getStart(), toIdx));
            } else {
                dataProvider.updateRowData(rg.getStart(),
                        new ArrayList<LibraryItem>());
            }
        }

    };

    public LibraryProvider(DeejaydUIWidget ui, String libType) {
        this(ui, libType, false);
    }

    public LibraryProvider(DeejaydUIWidget ui, String libType,
            boolean parentItem) {
        this.ui = ui;
        this.libType = libType;
        this.withParentItem = parentItem;
    }

    public AsyncDataProvider<LibraryItem> getDataProvider() {
        return dataProvider;
    }

    public String getPath() {
        return currentPath;
    }

    public void setPath(String path) {
        if (!path.equals(currentPath))
            updateItemList(path);
    }

    public void addPathChangeHandler(PathChangeHandler handler) {
        handlers.add(handler);
    }

    public void onLibraryChange(LibraryChangeEvent event) {
        updateItemList("");
    }

    private void updateItemList(String path) {
        currentPath = path;
        ui.rpc.libGetDirectory(libType, path,
                new AnswerHandler<FileDirList>() {

            public void onAnswer(FileDirList answer) {
                currentList.clear();
                if (!currentPath.equals("") && withParentItem)
                    currentList.add(new LibraryItem("", getParentPath(), ".."));

                for (String dir : answer.getDirectories())
                    currentList.add(new LibraryItem(currentPath, dir));

                if ("audio".equals(libType)) {
                    for (Media m : answer.getFiles())
                        currentList.add(new LibraryItem(currentPath, m));
                }

                dataProvider.updateRowCount(currentList.size(), true);
                dataProvider.updateRowData(0, currentList);

                for (PathChangeHandler handler : handlers) {
                    handler.onPathChange(answer.getRootPath());
                }
            }
        });
    }

    private String getParentPath() {
        if (!currentPath.equals("")) {
            String[] paths = currentPath.split("/");
            String path = "";
            if (paths.length > 1) {
                path = paths[0];
                for (int idx=1; idx<(paths.length-1); idx++)
                    path += "/"+paths[idx];
            }

            return path;
        }
        return "";
    }
}

//vim: ts=4 sw=4 expandtab