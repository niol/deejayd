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

package org.mroy31.deejayd.webui.cellview;

import java.util.ArrayList;
import java.util.List;

import org.mroy31.deejayd.common.provider.WebCategoryProvider;
import org.mroy31.deejayd.common.provider.WebCategoryProvider.Category;
import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.webui.client.WebuiLayout;
import org.mroy31.deejayd.webui.resources.WebuiResources;

import com.google.gwt.cell.client.AbstractCell;
import com.google.gwt.cell.client.ValueUpdater;
import com.google.gwt.core.client.GWT;
import com.google.gwt.dom.client.Element;
import com.google.gwt.dom.client.NativeEvent;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.cellview.client.Column;
import com.google.gwt.user.cellview.client.DeejaydCellTable;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.AbstractImagePrototype;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.ScrollPanel;
import com.google.gwt.user.client.ui.Widget;

public class WCategoryList extends Composite {
	private WebuiLayout ui;

	private static WCategoryListUiBinder uiBinder = GWT
			.create(WCategoryListUiBinder.class);
	interface WCategoryListUiBinder extends UiBinder<Widget, WCategoryList> {}
	
	/**
	 * RemoveButtonCell
	 * Cell that display a button to remove a category
	 * @author roy
	 *
	 */
	class RemoveButtonCell extends AbstractCell<Category> {
		
		public RemoveButtonCell() {
			super("click");
		}
		
		@Override
		public void render(Context context, Category value, SafeHtmlBuilder sb) {
			if (value.getId() != -1) {
				String img = AbstractImagePrototype.create(resources.clear()).getHTML();
				sb.appendHtmlConstant("<span class='"+
					resources.webuiCss().pointerCursor()+
					"' style='margin-left:6px;margin-right:6px;'>");
				sb.appendHtmlConstant(img);
				sb.appendHtmlConstant("</span>");
			}
		}
		
		@Override
	    public void onBrowserEvent(Context context, Element parent, Category value,
	              NativeEvent event, ValueUpdater<Category> valueUpdater) {
			if ("click".equals(event.getType())) {
				boolean confirm = Window.confirm(
	                    ui.i18nMessages.wbCatEraseConfirm(value.getName()));
				if (confirm) {
					ArrayList<Integer> ids = new ArrayList<Integer>();
					ids.add(value.getId());
					final Category erasedCategory = value;
										
					ui.rpc.wbModeRemoveCategories(selectedSource, ids, 
							new AnswerHandler<Boolean>() {
								
								@Override
								public void onAnswer(Boolean answer) {
									updateList(selectedSource, selectedCategoryId);
									if (erasedCategory.getId() == selectedCategoryId) 
										ui.update();
								}
					});
				}
			}
		}
	}
	
	/**
	 * CategoryCell
	 * Cell that display the name of the categorie
	 * When you click on it, 
	 * @author roy
	 *
	 */
	class CategoryCell extends AbstractCell<Category> {

		public CategoryCell() {
			super("click");
		}
		
		@Override
		public void render(com.google.gwt.cell.client.Cell.Context context,
				Category value, SafeHtmlBuilder sb) {
			sb.appendHtmlConstant("<span class='"+
				resources.webuiCss().pointerCursor()+
				"' style='margin:4px 10px;'>");
			if (value.getId() == -1) {
				sb.appendEscaped(ui.i18nConstants.all());
			} else {
				sb.appendEscaped(value.getName());
			}
			sb.appendHtmlConstant("</span>");
		}
		
		@Override
	    public void onBrowserEvent(Context context, Element parent, Category value,
	              NativeEvent event, ValueUpdater<Category> valueUpdater) {
			if ("click".equals(event.getType())) {
				ui.rpc.wbModeSetSourceCategorie(value.getId(), 
						new AnswerHandler<Boolean>() {

							@Override
							public void onAnswer(Boolean answer) {
								ui.update();
							}
				});
			}
		}
	}
	
	/*
	 * UiFields extract from ui.xml file
	 */
	@UiField Label categoryTitle;
	@UiField ScrollPanel categoryListPanel;
	@UiField(provided = true) DeejaydCellTable<Category> categoryList;
	@UiField(provided = true) final WebuiResources resources;
	
	/*
	 * Constants
	 */
    private WebCategoryProvider provider;
    private int selectedCategoryId = -1;
    private String selectedSource = null;
    // optionnal remove column
    private Column<Category, Category> rButtonColumn = new Column<Category, Category>(
    		new RemoveButtonCell()) {

		@Override
		public Category getValue(Category object) {
			return (object == null) ? null : object;
		}
	};
	private boolean isRmColumnPresent = false;

	public WCategoryList(WebuiLayout webui) {
		this.ui = webui;
		resources = webui.resources;
		
		provider = new WebCategoryProvider(ui);
        categoryList = new DeejaydCellTable<Category>(1000, provider.getKeyProvider());
        
        provider.getDataProvider().addDataDisplay(categoryList);
        categoryList.setSelectionModel(provider.getSelectionModel());
        
		initWidget(uiBinder.createAndBindUi(this));
		categoryTitle.setText(ui.i18nConstants.wbCategories());
		
		categoryList.addColumn(new Column<WebCategoryProvider.Category, Category>(
				new CategoryCell()) {

			@Override
			public Category getValue(Category object) {
				return object;
			}
		});
	}

	public void updateList(String source, int cat) {
		if (source != "local" && isRmColumnPresent) {
			categoryList.removeColumn(rButtonColumn);
			isRmColumnPresent = false;
		} else if (source == "local" && !isRmColumnPresent) {
			categoryList.addColumn(rButtonColumn);
			categoryList.setColumnWidth(1, "40px");
			isRmColumnPresent = true;
		}
		
		selectedCategoryId = cat;
		selectedSource = source;
		
		provider.updateList(source, selectedCategoryId);
	}
	
	public void updateSelectedCategory(int cat) {
		if (cat != selectedCategoryId) {
			selectedCategoryId = cat;
			provider.updateSelectedCategory(cat);
		}
	}
	
	public List<Category> getCategoryList() {
		return provider.getCurrentList();
	}
}

//vim: ts=4 sw=4 expandtab