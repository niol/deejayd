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

package org.mroy31.deejayd.mobile.sources;

import java.util.HashMap;

import org.mroy31.deejayd.common.rpc.DefaultRpcCallback;
import org.mroy31.deejayd.common.rpc.NullRpcCallback;
import org.mroy31.deejayd.mobile.client.MobileLayout;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.user.client.Command;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.ListBox;
import com.google.gwt.user.client.ui.HTMLTable.RowFormatter;

public class OptionPanel extends Composite {
    private final MobileLayout ui = MobileLayout.getInstance();
    private final String source;
    private final Command saveCmd;

    private Grid optionGrid = new Grid(2, 2);
    private Label rLabel = new Label(ui.i18nConst.repeat());
    private Label pLabel = new Label(ui.i18nConst.playOrder());
    private CheckBox repeat = new CheckBox();
    private ListBox playorder = new ListBox();
    private Label saveButton = new Label(ui.i18nConst.save());

    public OptionPanel(String s, Command onSave) {
        this.source = s;
        this.saveCmd = onSave;

        FlowPanel panel = new FlowPanel();
        panel.setWidth("100%");
        optionGrid.setWidth("100%");
        optionGrid.setCellPadding(3);
        optionGrid.setCellSpacing(5);
        RowFormatter f = optionGrid.getRowFormatter();
        f.setVerticalAlign(0, HorizontalPanel.ALIGN_MIDDLE);
        f.setVerticalAlign(1, HorizontalPanel.ALIGN_MIDDLE);

        playorder.addItem(ui.i18nConst.inOrder(), "inorder");
        playorder.addItem(ui.i18nConst.random(), "random");
        playorder.addItem(ui.i18nConst.oneMedia(), "onemedia");

        saveButton.addStyleName(ui.resources.mobileCss().button());
        saveButton.addStyleName(ui.resources.mobileCss().center());
        saveButton.setWidth("100%");
        saveButton.addClickHandler(new ClickHandler() {
            @Override
            public void onClick(ClickEvent event) {
                save();
            }
        });

        optionGrid.setWidget(0, 0, rLabel);
        optionGrid.setWidget(0, 1, repeat);
        optionGrid.setWidget(1, 0, pLabel);
        optionGrid.setWidget(1, 1, playorder);
        panel.add(optionGrid);
        panel.add(saveButton);

        initWidget(panel);
    }

    public void update(HashMap<String, String> status) {
        boolean rValue = Boolean.parseBoolean(status.get(source+"repeat"));
        if (repeat.getValue() != rValue) {
            repeat.setValue(rValue);
        }

        String pValue = status.get(source+"playorder");
        if (!pValue.equals(playorder.getValue(playorder.getSelectedIndex()))) {
            for (int idx=0; idx<playorder.getItemCount(); idx++) {
                if (pValue.equals(playorder.getValue(idx))) {
                    playorder.setSelectedIndex(idx);
                    break;
                }
            }
        }
    }

    public void save() {
        ui.rpc.setOption(source, "playorder",
                playorder.getValue(playorder.getSelectedIndex()),
                new NullRpcCallback(ui));
        ui.rpc.setOption(source, "repeat",
                repeat.getValue(), new DefaultRpcCallback(ui));

        saveCmd.execute();
    }

}

//vim: ts=4 sw=4 expandtab