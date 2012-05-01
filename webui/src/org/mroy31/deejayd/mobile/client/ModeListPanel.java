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

package org.mroy31.deejayd.mobile.client;

import java.util.ArrayList;
import java.util.HashMap;

import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.mobile.widgets.WallToWallPanel;

import com.google.gwt.cell.client.ClickableTextCell;
import com.google.gwt.cell.client.ValueUpdater;
import com.google.gwt.user.cellview.client.CellList;
import com.google.gwt.user.cellview.client.HasKeyboardSelectionPolicy.KeyboardSelectionPolicy;

public class ModeListPanel extends WallToWallPanel {

    public ModeListPanel() {
        super("Mode List", null);       
        final CellList<String> panel = new CellList<String>(new ClickableTextCell(), ui.cellListRessources);
        panel.setValueUpdater(new ValueUpdater<String>() {
			
			@Override
			public void update(String value) {
				ui.rpc.setMode(value, new AnswerHandler<Boolean>() {
                    public void onAnswer(Boolean answer) {
                        ui.update();
                        showChild();
                    }
                });
			}
		});
        panel.setKeyboardSelectionPolicy(KeyboardSelectionPolicy.DISABLED);
        add(panel);

        // build mode list
        ui.rpc.getModeList(new AnswerHandler<HashMap<String,String>>() {
            public void onAnswer(HashMap<String, String> list) {
            	ArrayList<String> modes = new ArrayList<String>();
                for (String key : list.keySet()) {               	
                    if (list.get(key).equals("true")) {
                        modes.add(key);
                    }                   
                }
                panel.setRowData(modes);
            }
        });
    }

    @Override
    protected String getShortTitle() {
        return ui.i18nConst.list();
    }

}

//vim: ts=4 sw=4 expandtab