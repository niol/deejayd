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

package org.mroy31.deejayd.webui.widgets;

import java.util.HashMap;

import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.webui.client.WebuiLayout;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.user.client.Command;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.DialogBox;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

public class NewWbCatDialog extends DialogBox {
    private final WebuiLayout ui = WebuiLayout.getInstance();
    private TextBox input;
    private Command cmd;

    public NewWbCatDialog(Command onFinish) {
    	cmd = onFinish;
    	
        // Set the dialog box's caption.
        setText(ui.i18nConstants.wbAddCatDialog());
        // Enable animation.
        setAnimationEnabled(true);
        // Enable glass background.
        setGlassEnabled(true);

        VerticalPanel panel = new VerticalPanel();
        panel.setSpacing(2);
        HorizontalPanel buttonPanel = new HorizontalPanel();
        buttonPanel.setSpacing(3);

        input = new TextBox();
        panel.add(input);

        Button cancel = new Button(ui.i18nConstants.cancel(), new ClickHandler() {
            public void onClick(ClickEvent event) {
                NewWbCatDialog.this.hide();
            }
        });
        buttonPanel.add(cancel);
        Button save = new Button(ui.i18nConstants.save(), new ClickHandler() {
            public void onClick(ClickEvent event) {
                if (!input.getValue().equals("")) {
                    ui.rpc.wbModeAddCategory("local", input.getValue(), 
                    		new AnswerHandler<HashMap<String,String>>() {
								
								public void onAnswer(HashMap<String, String> answer) {
									NewWbCatDialog.this.hide();
				                    cmd.execute();
								}
					});                 
                }
            }
        });
        buttonPanel.add(save);
        panel.setHorizontalAlignment(VerticalPanel.ALIGN_RIGHT);
        panel.add(buttonPanel);

        setWidget(panel);
    }

    @Override
    public void center() {
        input.setValue("");
        super.center();
    }
}

//vim: ts=4 sw=4 expandtab