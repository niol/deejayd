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

public class LibraryProvider implements LibraryChangeHandler {
    private final DeejaydUIWidget ui;
    private final String libType;

    public static class LibraryItem {
        private String path;
        private String type;
        private Media file;
        private String dir;

        public LibraryItem(String root, String dir) {
            this.type = "directory";
            this.path = root.equals("") ? dir : root + "/" + dir;
            this.dir = dir;
        }

        public LibraryItem(String root, Media m) {
            this.type = "file";
            this.path = root.equals("") ? m.getStrAttr("filename") :
                root + "/" + m.getStrAttr("filename");
            this.file = m;
        }

        public String getLabel() {
            if ("directory".equals(type))
                return dir;
            else if ("file".equals(type))
                return file.getStrAttr("filename");
            return "";
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
        }

    };

    public LibraryProvider(DeejaydUIWidget ui, String libType) {
        this.ui = ui;
        this.libType = libType;
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

    public void onLibraryChange(LibraryChangeEvent event) {
        updateItemList("");
    }

    private void updateItemList(String path) {
        currentPath = path;
        ui.rpc.libGetDirectory(libType, path,
                new AnswerHandler<FileDirList>() {

            public void onAnswer(FileDirList answer) {
                currentList.clear();
                for (String dir : answer.getDirectories())
                    currentList.add(new LibraryItem(currentPath, dir));
                for (Media m : answer.getFiles())
                    currentList.add(new LibraryItem(currentPath, m));

                dataProvider.updateRowCount(currentList.size(), true);
                dataProvider.updateRowData(0, currentList);
            }
        });
    }
}

//vim: ts=4 sw=4 expandtab