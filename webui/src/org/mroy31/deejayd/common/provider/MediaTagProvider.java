/*
 * Deejayd, a media player daemon
 * Copyright (C) 2007-2011 Mickael Royer <mickael.royer@gmail.com>
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
import java.util.List;

import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.common.rpc.types.ComplexFilter;
import org.mroy31.deejayd.common.widgets.DeejaydUIWidget;

import com.google.gwt.view.client.AsyncDataProvider;
import com.google.gwt.view.client.HasData;
import com.google.gwt.view.client.ProvidesKey;
import com.google.gwt.view.client.Range;

public class MediaTagProvider {
	
	public class MediaTag {
		private String name;
		private String value;
		private String type;
		
		public MediaTag(String name, String value, String type) {
			this.name = name;
			this.value = value;
			this.type = type;
		}
		
		public String getName() {
			return this.name;
		}
		
		public String getValue() {
			return this.value;
		}
		
		public String getType() {
			return this.type;
		}
	}
	
	private final DeejaydUIWidget ui;

	/*
	 * Private variables
	 */
	private ProvidesKey<MediaTag> keyProvider = new ProvidesKey<MediaTag>() {

        public Object getKey(MediaTag item) {
            // Always do a null check.
            return (item == null) ? "" : item.getValue();
        }
    };
	private ArrayList<MediaTag> currentList = new ArrayList<MediaTag>();
	private AsyncDataProvider<MediaTag> dataProvider=new AsyncDataProvider<MediaTag>() {

        @Override
        protected void onRangeChanged(HasData<MediaTag> display) {
            Range rg = display.getVisibleRange();
            if (currentList.size() > rg.getStart()) {
                int toIdx = Math.min(currentList.size()-1,
                        rg.getStart()+rg.getLength());
                dataProvider.updateRowData(rg.getStart(),
                        currentList.subList(rg.getStart(), toIdx));
            } else {
                dataProvider.updateRowData(rg.getStart(),
                        new ArrayList<MediaTag>());
            }
        }

    };
    
	public MediaTagProvider(DeejaydUIWidget ui) {
        this.ui = ui;
    }
	
	public AsyncDataProvider<MediaTag> getDataProvider() {
        return dataProvider;
    }
	
	public ProvidesKey<MediaTag> getKeyProvider() {
		return keyProvider;
	}
	
	public void updateList(final String tag, ComplexFilter filter) {
		ui.rpc.audioLibTagList(tag, filter, new AnswerHandler<List<String>>() {

            public void onAnswer(List<String> answer) {
            	currentList.clear();
            	currentList.add(new MediaTag(ui.getI18nConstants().all(), "__all__", tag));
            	
            	for (String tagValue : answer) {
            		String name = tagValue;
            		if (tagValue.equals("__various__")) {
            			name = ui.getI18nConstants().variousArtist();
            		} else if (tagValue.equals("")) {
            			name = ui.getI18nConstants().unknown();
            		}
            		currentList.add(new MediaTag(name, tagValue, tag));
            	}
            	
            	dataProvider.updateRowCount(currentList.size(), true);
                dataProvider.updateRowData(0, currentList);
            }
            
        });
	}
	
	public List<MediaTag> getCurrentList() {
		return currentList;
	}
}
