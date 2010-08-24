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

public class MagicPlsDialog extends DialogBox {
    private final WebuiLayout ui = WebuiLayout.getInstance();
    private MagicPlsDialogContent dgContent;

    public MagicPlsDialog() {
        setAnimationEnabled(true);
        setModal(true);
        setGlassEnabled(true);

        dgContent = new MagicPlsDialogContent();
        setWidget(dgContent);

        Button canc = new Button(ui.i18nConstants.cancel(), new ClickHandler() {
            public void onClick(ClickEvent event) {
                hide();
            }
        });
        Button save = new Button(ui.i18nConstants.save(), new ClickHandler() {
            public void onClick(ClickEvent event) {
                dgContent.save();
                hide();
            }
        });
        dgContent.addActionButton(canc);
        dgContent.addActionButton(save);
    }

    public void load(String name, String id) {
        load(name, id, false);
    }

    public void load(String name, String id, boolean loadFilter) {
        setText(ui.i18nMessages.magicPlsDgCaption(name));
        dgContent.load(id, loadFilter);
    }
}

//vim: ts=4 sw=4 expandtab