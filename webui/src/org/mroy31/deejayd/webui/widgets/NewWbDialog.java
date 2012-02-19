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

package org.mroy31.deejayd.webui.widgets;

import java.util.List;

import org.mroy31.deejayd.common.provider.WebCategoryProvider.Category;
import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.webui.client.WebuiLayout;
import org.mroy31.deejayd.webui.resources.WebuiResources;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.DialogBox;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.ListBox;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.Widget;

/**
 * NewWbDialog
 * A dialog box to add new webradio
 * @author roy
 *
 */
public class NewWbDialog extends Composite {
	private final WebuiLayout ui = WebuiLayout.getInstance();

	private static NewWbDialogUiBinder uiBinder = GWT
			.create(NewWbDialogUiBinder.class);
	interface NewWbDialogUiBinder extends UiBinder<Widget, NewWbDialog> {}

	/*
	 * UiFields extracted from .ui.xml file
	 */
	@UiField DialogBox dialog;
    @UiField Label nameLabel;
    @UiField TextBox nameInput;
    @UiField Label urlLabel;
    @UiField TextBox urlInput;
    @UiField Label catLabel;
    @UiField ListBox catInput;
    @UiField Button addButton;
    @UiField Button cancelButton;
    @UiField(provided = true) final WebuiResources resources;
    
    /**
     * NewWbDialog Constructor
     * Construct a dialog to add new webradio
     */
	public NewWbDialog() {
		resources = ui.resources;		
		initWidget(uiBinder.createAndBindUi(this));
		
        nameLabel.setText(ui.i18nConstants.wbName());
        urlLabel.setText(ui.i18nConstants.wbUrl());
        catLabel.setText(ui.i18nConstants.wbCategory());

        cancelButton.setText(ui.i18nConstants.cancel());
        cancelButton.addClickHandler(new ClickHandler() {
			
			public void onClick(ClickEvent event) {
				dialog.hide();
			}
		});
        addButton.setText(ui.i18nConstants.add());
        addButton.addClickHandler(new ClickHandler() {
            public void onClick(ClickEvent event) {
                String name = nameInput.getValue();
                String url = urlInput.getValue();
                if (!name.equals("") && !url.equals("")) {
                	String cat = catInput.getValue(catInput.getSelectedIndex());
                    ui.rpc.wbModeAddWebradio("local", name, url, cat, new AnswerHandler<Boolean>() {

                        public void onAnswer(Boolean answer) {
                        	nameInput.setValue("");
                            urlInput.setValue("");
                            ui.update();
                            dialog.hide();
                            
                            ui.setMessage(ui.i18nConstants.wbAddConfirmation());
                        }
                    });
                }
            }
        });
	}

	public void updateCategoryList(List<Category> categories) {
		while (catInput.getItemCount() > 0)
			catInput.removeItem(0);
		
		for (Category cat : categories) {
			if (cat.getId() != -1)
				catInput.addItem(cat.getName(), Integer.toString(cat.getId()));
		}
	}
	
	/**
	 * Show the dialog box
	 */
	public void show() {
		dialog.center();
	}
	
}

//vim: ts=4 sw=4 expandtab