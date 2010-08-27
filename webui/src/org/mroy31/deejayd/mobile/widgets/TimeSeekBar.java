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

package org.mroy31.deejayd.mobile.widgets;

import org.mroy31.deejayd.common.widgets.DeejaydUtils;
import org.mroy31.deejayd.mobile.client.MobileLayout;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.HasValue;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.Widget;

public class TimeSeekBar extends Composite
        implements ClickHandler, HasValue<Integer> {
    protected final MobileLayout ui = MobileLayout.getInstance();
    private int value = 0;
    private int maxValue = 0;

    private Label timeDesc = new Label();
    private Button fastRwdButton = new Button();
    private Button rwdButton = new Button();
    private Button fastFwdButton = new Button();
    private Button fwdButton = new Button();

    public TimeSeekBar() {
        HorizontalPanel rootPanel = new HorizontalPanel();
        rootPanel.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);

        for (Button btn : new Button[]{fastRwdButton, rwdButton,
                fwdButton, fastFwdButton}) {
            btn.addClickHandler(this);
            btn.addStyleName(ui.resources.mobileCss().playerButton());
        }
        fastRwdButton.addStyleName(ui.resources.mobileCss().goFirst());
        rootPanel.add(fastRwdButton);
        rwdButton.addStyleName(ui.resources.mobileCss().goPrevious());
        rootPanel.add(rwdButton);
        timeDesc.addStyleName(ui.resources.mobileCss().seekBarDesc());
        rootPanel.add(timeDesc);
        fwdButton.addStyleName(ui.resources.mobileCss().goNext());
        rootPanel.add(fwdButton);
        fastFwdButton.addStyleName(ui.resources.mobileCss().goLast());
        rootPanel.add(fastFwdButton);

        initWidget(rootPanel);
        updateDesc();
    }

    public void onClick(ClickEvent event) {
        Widget sender = (Widget) event.getSource();
        if (sender == fastRwdButton) {
            setValue(value-60);
        } else if (sender == rwdButton) {
            setValue(value-5);
        } else if (sender == fwdButton) {
            setValue(value+5);
        } else if (sender == fastFwdButton) {
            setValue(value+60);
        }
    }

    public Integer getValue() {
        return value;
    }

    public void setValue(Integer value) {
        setValue(value, true);
    }

    public void setValue(Integer value, boolean fireEvents) {
        if (value != this.value) {
            this.value = value;
            updateDesc();
            if (fireEvents) {
                ValueChangeEvent.fire(this, this.value);
            }
        }
    }

    public HandlerRegistration addValueChangeHandler(
            ValueChangeHandler<Integer> handler) {
        return addHandler(handler, ValueChangeEvent.getType());
    }

    public Integer getMaxValue() {
        return maxValue;
    }

    public void setMaxValue(int maxValue) {
        if (maxValue != this.maxValue) {
            this.maxValue = maxValue;
            updateDesc();
        }
    }

    private void updateDesc() {
        timeDesc.setText(DeejaydUtils.formatTime(value)+" / "+
                DeejaydUtils.formatTime(maxValue));
    }
}

//vim: ts=4 sw=4 expandtab