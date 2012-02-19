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

package org.mroy31.deejayd.webui.client;

import java.util.HashMap;

import org.mroy31.deejayd.common.events.StatusChangeEvent;
import org.mroy31.deejayd.common.events.StatusChangeHandler;
import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.webui.cellview.WCategoryList;
import org.mroy31.deejayd.webui.resources.WebuiResources;
import org.mroy31.deejayd.webui.widgets.NewWbCatDialog;
import org.mroy31.deejayd.webui.widgets.NewWbDialog;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ChangeEvent;
import com.google.gwt.event.dom.client.ChangeHandler;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiFactory;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.Command;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.ListBox;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.Widget;

public class WebradioPanel extends WebuiPanel implements StatusChangeHandler {

    private static WebradioPanelUiBinder uiBinder = GWT
            .create(WebradioPanelUiBinder.class);

    interface WebradioPanelUiBinder extends UiBinder<Widget, WebradioPanel> { }

    @UiField Label panelTitle;
    @UiField ListBox sourceListBox;
    @UiField HorizontalPanel categoriesToolbar;
    @UiField Button addCatButton;
    
    @UiField Button addButton;
    @UiField(provided = true) WCategoryList categoryList;
    @UiField(provided = true) final WebuiResources resources;

    private WebuiLayout ui;
    private String source = null;
    private int categorie = -1;
    private HashMap<String, Boolean> sourceList = new HashMap<String, Boolean>();
    private NewWbDialog newWbDialog = new NewWbDialog();
    private NewWbCatDialog newWbCatDialog = new NewWbCatDialog(new Command() {
		
		public void execute() {
			categoryList.updateList(source, categorie);
		}
	});
    
    private class OnSourceChange implements ChangeHandler {
        private WebuiLayout ui;

        public OnSourceChange(WebuiLayout webui) {
            ui = webui;
        }

        public void onChange(ChangeEvent event) {
            String source = sourceListBox.getValue(
                    sourceListBox.getSelectedIndex());
            ui.rpc.wbModeSetSource(source, null);
        }
    }

    /**
     * WebuiPanel constructor
     * @param webui
     */
    public WebradioPanel(WebuiLayout webui) {
        super("webradio");
        resources = webui.resources;
        ui = webui;
        categoryList = new WCategoryList(ui);
        
        initWidget(uiBinder.createAndBindUi(this));
        
        panelTitle.setText(ui.i18nConstants.wbCurrentSource());
    
        addButton.setText(ui.i18nConstants.wbAdd());
        addButton.addClickHandler(new ClickHandler() {

			public void onClick(ClickEvent event) {
				if (categoryList.getCategoryList().size() == 1) {
					Window.alert(ui.i18nConstants.wbAddError());
				} else {
					newWbDialog.updateCategoryList(categoryList.getCategoryList());
					newWbDialog.show();
				}
			}
        	
        });
        
        addCatButton.setText(ui.i18nConstants.wbAddCat());
        addCatButton.addClickHandler(new ClickHandler() {

			public void onClick(ClickEvent event) {
				newWbCatDialog.center();
			}
        	
        });

        ui.addStatusChangeHandler(this);
    }


    @UiFactory public TextBox makeWbTextBox() {
        TextBox box = new TextBox();
        box.setVisibleLength(12);
        box.setMaxLength(128);

        return box;
    }

    private int __updateCategoryValue(HashMap<String, String> status) {
    	int cat;
    	try {
        	cat = Integer.parseInt(status.get("webradiosourcecat"));
        } catch (Exception e){
        	cat = -1;
        }
    	
    	return cat;
    }
    
    public void onStatusChange(StatusChangeEvent event) {
        HashMap<String, String> status = event.getStatus();
        if (source == null) {
            // add current source in sourceList
            source = status.get("webradiosource");
            categorie = __updateCategoryValue(status);
            ui.rpc.wbModeGetSources(new AnswerHandler<HashMap<String,String>>() {

                public void onAnswer(HashMap<String, String> answer) {
                    for (String key : answer.keySet()) {
                        boolean hasCat = Boolean.parseBoolean(answer.get(key));
                        sourceList.put(key, hasCat);
                        sourceListBox.addItem(getSourceName(key), key);
                    }
                    sourceListBox.addChangeHandler(new OnSourceChange((WebuiLayout)ui));
                    updatePanel();
                }
            });
        } else if (!source.equals(status.get("webradiosource"))) {
            source = status.get("webradiosource");
            categorie = __updateCategoryValue(status);
            updatePanel();
        } else {
        	int cat = __updateCategoryValue(status);
        	if (cat != categorie) {
	            // Select current category
	        	categorie = cat;
	            categoryList.updateSelectedCategory(categorie);
        	}
        }
    }

    private void updatePanel() {
        if (!source.equals(
                sourceListBox.getValue(sourceListBox.getSelectedIndex()))) {
            for (int idx=0; idx<sourceListBox.getItemCount(); idx ++) {
                if (source.equals(sourceListBox.getValue(idx))) {
                    sourceListBox.setSelectedIndex(idx);
                    break;
                }
            }
        }

        // display form and enable cat button only for local source
        addButton.setEnabled(source.equals("local"));
        addCatButton.setEnabled(source.equals("local"));
        
        // update categories list
        categoryList.updateList(source, categorie);       
    }

    private String getSourceName(String sourceName) {
        if (sourceName.equals("local")) {
            return ui.i18nConstants.wbLocalSource();
        } else if (sourceName.equals("icecast")) {
            return ui.i18nConstants.wbIcecastSource();
        }
        return sourceName;
    }
}

//vim: ts=4 sw=4 expandtab