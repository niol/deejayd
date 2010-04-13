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

import org.mroy31.deejayd.webui.client.WebuiLayout;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.DialogBox;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

public class NewPlsDialog extends DialogBox {
    private final WebuiLayout ui = WebuiLayout.getInstance();
    private TextBox input;
    public interface PlsCommand {
        public void execute(String plsName);
    }
    private PlsCommand command;

    public NewPlsDialog(PlsCommand cmd) {
        command = cmd;
        // Set the dialog box's caption.
        setText(ui.i18nConstants.newPlsDgCaption());
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

        Button cancel = new Button(ui.i18nConstants.cancel());
        cancel.addClickHandler(new ClickHandler() {
            public void onClick(ClickEvent event) {
                NewPlsDialog.this.hide();
            }
        });
        buttonPanel.add(cancel);
        Button save = new Button(ui.i18nConstants.save());
        save.addClickHandler(new ClickHandler() {
            public void onClick(ClickEvent event) {
                if (!input.getValue().equals("")) {
                    command.execute(input.getValue());
                    NewPlsDialog.this.hide();
                }
            }
        });
        buttonPanel.add(save);
        panel.setHorizontalAlignment(VerticalPanel.ALIGN_RIGHT);
        panel.add(buttonPanel);

        setWidget(panel);
    }

    public void center() {
        input.setValue("");
        super.center();
    }
}

//vim: ts=4 sw=4 expandtab