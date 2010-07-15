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

import org.mroy31.deejayd.common.events.StatusChangeEvent;
import org.mroy31.deejayd.common.rpc.DefaultRpcCallback;
import org.mroy31.deejayd.mobile.client.MobileLayout;

import com.google.gwt.event.dom.client.ChangeEvent;
import com.google.gwt.event.dom.client.ChangeHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.ListBox;

public abstract class DefaultDeejaydMode extends DeejaydMode {
    protected final MobileLayout ui = MobileLayout.getInstance();
    protected String name;
    protected int sourceId = -1;
    protected MediaList mediaList;

    protected class OptionPanel extends Composite {
        private CheckBox rptCk;
        private ListBox pOdrList;

        public OptionPanel() {
            this(true, true);
        }

        public OptionPanel(boolean hasRepeat, boolean hasPlayorder) {
            FlowPanel panel = new FlowPanel();

            if (hasRepeat) {
                rptCk = new CheckBox(ui.i18nConst.repeat());
                rptCk.addValueChangeHandler(new ValueChangeHandler<Boolean>() {
                    @Override
                    public void onValueChange(ValueChangeEvent<Boolean> event) {

                    }
                });

                panel.add(rptCk);
            }

            if (hasPlayorder) {
                FlowPanel pOrderPanel = new FlowPanel();

                pOdrList = new ListBox();
                pOdrList.addItem(ui.i18nConst.inOrder(), "inorder");
                pOdrList.addItem(ui.i18nConst.random(), "random");
                pOdrList.addItem(ui.i18nConst.oneMedia(), "onemedia");
                pOdrList.addChangeHandler(new ChangeHandler() {
                    @Override
                    public void onChange(ChangeEvent event) {
                        ui.rpc.setOption(name, "playorder",
                            pOdrList.getValue(pOdrList.getSelectedIndex()),
                            new DefaultRpcCallback(ui));
                    }
                });

                pOrderPanel.add(pOdrList);
                pOrderPanel.add(new Label(ui.i18nConst.player()));
            }

            initWidget(panel);
        }

        public void setRepeat(boolean repeat) {
            if (rptCk != null) {
                rptCk.setValue(repeat);
            }
        }

        public void setPlayorder(String value) {
            if (pOdrList != null) {
                for (int i=0; i<pOdrList.getItemCount(); i++) {
                    if (pOdrList.getValue(i).equals(value))
                        pOdrList.setSelectedIndex(i);
                }
            }
        }

        public boolean getRepeat() {
            return rptCk != null ? rptCk.getValue() : null;
        }

        public String getPlayOrder() {
            return pOdrList != null ?
                    pOdrList.getValue(pOdrList.getSelectedIndex()) : "";
        }
    }

    public DefaultDeejaydMode(String name) {
        this.name = name;
        this.mediaList = initMediaList();


        FlowPanel panel = new FlowPanel();
        panel.add(mediaList);
        initWidget(panel);

        ui.addStatusChangeHandler(this);
    }

    @Override
    public void onStatusChange(StatusChangeEvent event) {
        int id = Integer.parseInt(event.getStatus().get(name));
        if (id != sourceId) {
            mediaList.updateList(
                    Integer.parseInt(event.getStatus().get(name+"length")));
            sourceId = id;
        }
    }

    abstract public MediaList initMediaList();
}

//vim: ts=4 sw=4 expandtab