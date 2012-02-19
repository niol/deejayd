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
import java.util.HashMap;
import java.util.List;
import java.util.TreeMap;

import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.common.widgets.DeejaydSelModel;
import org.mroy31.deejayd.common.widgets.DeejaydUIWidget;

import com.google.gwt.view.client.AsyncDataProvider;
import com.google.gwt.view.client.HasData;
import com.google.gwt.view.client.ProvidesKey;
import com.google.gwt.view.client.Range;

public class WebCategoryProvider {
	private final DeejaydUIWidget ui;
	
	/**
	 * Category
	 * Object that represents a webradio category
	 * @author roy
	 *
	 */
	public class Category {
    	private int id;
    	private String name;
    	
    	public Category(int cat_id, String cat_name) {
    		this.id = cat_id;
    		this.name = cat_name;
    	}
    	
    	public int getId() {
    		return this.id;
    	}
    	
    	public String getName() {
    		return this.name;
    	}
    }

	/*
	 * Private variables
	 */
	private ProvidesKey<Category> keyProvider = new ProvidesKey<Category>() {

        public Object getKey(Category item) {
            // Always do a null check.
            return (item == null) ? "" : item.getId();
        }
    };
    private Category selectedCategory = null;
	private DeejaydSelModel<Category> selModel = new DeejaydSelModel<Category>(keyProvider);
	private ArrayList<Category> currentList = new ArrayList<Category>();
	private AsyncDataProvider<Category> dataProvider=new AsyncDataProvider<Category>() {

        @Override
        protected void onRangeChanged(HasData<Category> display) {
            Range rg = display.getVisibleRange();
            if (currentList.size() > rg.getStart()) {
                int toIdx = Math.min(currentList.size()-1,
                        rg.getStart()+rg.getLength());
                dataProvider.updateRowData(rg.getStart(),
                        currentList.subList(rg.getStart(), toIdx));
            } else {
                dataProvider.updateRowData(rg.getStart(),
                        new ArrayList<Category>());
            }
        }

    };
    
	public WebCategoryProvider(DeejaydUIWidget ui) {
        this.ui = ui;
    }
	
	public AsyncDataProvider<Category> getDataProvider() {
        return dataProvider;
    }
	
	public ProvidesKey<Category> getKeyProvider() {
		return keyProvider;
	}
	
	public DeejaydSelModel<Category> getSelectionModel() {
		return selModel;
	}
	
	public void updateList(String source, final int selectedCatId) {		
		ui.rpc.wbModeGetSourceCategories(source,
                new AnswerHandler<HashMap<String, String>>() {

                    public void onAnswer(HashMap<String, String> answer) {
                    	currentList.clear();
                    	currentList.add(new Category(-1, "__all__"));
                        TreeMap<String, String> sortedAns = new TreeMap<String, String>(answer);

                        for (String cat : sortedAns.keySet()) {
                        	int id = Integer.parseInt(sortedAns.get(cat));
                        	currentList.add(new Category(id, cat));
                        }
                        
                        updateSelectedCategory(selectedCatId);
                        dataProvider.updateRowCount(currentList.size(), true);
                        dataProvider.updateRowData(0, currentList);
                    }
        });
		
	}
	
	public void updateSelectedCategory(int catId) {
		if (selectedCategory == null || selectedCategory.getId() != catId) {
			if (selectedCategory != null) {
				selModel.setSelected(selectedCategory, false);
			}
			
			for (Category cat : currentList) {
				if (cat.getId() == catId) {
					selectedCategory = cat;
					selModel.setSelected(cat, true);
					break;
				}
			}
		}
	}
	
	public List<Category> getCurrentList() {
		return currentList;
	}
}
