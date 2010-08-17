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

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;

import org.mroy31.deejayd.webui.client.WebuiLayout;
import org.mroy31.deejayd.webui.resources.WebuiResources;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.dom.client.KeyCodes;
import com.google.gwt.event.logical.shared.HasValueChangeHandlers;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiFactory;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.DOM;
import com.google.gwt.user.client.Event;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.HasValue;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.ScrollPanel;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.google.gwt.user.client.ui.Widget;

public class TagList extends Composite
        implements HasValueChangeHandlers<String[]>, HasValue<String[]> {
    private WebuiLayout ui;
    private boolean ctrlKey = false;
    private ArrayList<String> values = new ArrayList<String>();
    private HashMap<String, Label> labelMap = new HashMap<String, Label>();

    private static TagListUiBinder uiBinder = GWT.create(TagListUiBinder.class);
    interface TagListUiBinder extends UiBinder<Widget, TagList> {}

    @UiField Label title;
    @UiField ScrollPanel scrollList;
    @UiField VerticalPanel tagList;
    @UiField(provided = true) final WebuiResources resources;

    private class ItemClickHandler implements ClickHandler {
        private String value;

        public ItemClickHandler(String value) { this.value = value; }
        @Override
        public void onClick(ClickEvent event) {
            if (value.equals("__all__")) {
                String[] result = {value};
                setValue(result);
            } else if (ctrlKey) {
                ArrayList<String> selected =
                    new ArrayList<String>(Arrays.asList(getValue()));
                selected.add(value);
                setValue(selected.toArray(new String[0]));
            } else {
                String[] result = {value};
                setValue(result);
            }
        }
    }

    public TagList(WebuiLayout webui, String tag) {
        this.ui = webui;
        this.resources = ui.resources;

        initWidget(uiBinder.createAndBindUi(this));
        setWidth("100%"); setHeight("100%");
        DOM.setStyleAttribute(title.getElement(), "textAlign", "center");
        title.setText(tag);

        sinkEvents(Event.MOUSEEVENTS | Event.KEYEVENTS);
    }

    public void setLoading() {
        tagList.clear();
        tagList.add(new LoadingWidget(ui.i18nConstants.loading(), resources));
    }

    public void setItems(JSONArray items) {
        tagList.clear();
        values.clear();
        labelMap.clear();

        Widget currentW = null;
        for (int idx=0; idx<items.size(); idx++) {
            JSONObject item = items.get(idx).isObject();

            Label lab = new Label(item.get("name").isString().stringValue());
            lab.setWidth("95%");
            lab.addStyleName(resources.webuiCss().tagPanelItem());
            String v = item.get("value").isString().stringValue();
            lab.addClickHandler(new ItemClickHandler(v));

            if (item.get("sel").isString().stringValue().equals("true")) {
                lab.addStyleName(resources.webuiCss().tagPanelSelectedItem());
                currentW = lab;
                values.add(v);
            }

            String cls = item.get("class").isString().stringValue();
            if (cls.equals("list-unknown"))
                lab.addStyleName(resources.webuiCss().italic());
            else if (cls.equals("list-all"))
                lab.addStyleName(resources.webuiCss().bold());

            labelMap.put(v, lab);
            tagList.add(lab);
        }

        if (currentW != null)
            scrollList.ensureVisible(currentW);

    }

    @UiFactory public ScrollPanel makeScrollPanel() {
        ScrollPanel panel = new ScrollPanel();
        DOM.setStyleAttribute(panel.getElement(), "overflowY", "scroll");
        DOM.setStyleAttribute(panel.getElement(), "overflowX", "hidden");

        return panel;
    }

    @Override
    public void onBrowserEvent(Event event) {
        super.onBrowserEvent(event);
        switch (DOM.eventGetType(event)) {
            case Event.ONKEYDOWN:
                switch (DOM.eventGetKeyCode(event)) {
                    case KeyCodes.KEY_CTRL:
                        ctrlKey = true;
                }
                break;
            case Event.ONKEYUP:
                ctrlKey = false;
                break;
        }
    }

    @Override
    public HandlerRegistration addValueChangeHandler(
            ValueChangeHandler<String[]> handler) {
        return addHandler(handler, ValueChangeEvent.getType());
    }

    @Override
    public String[] getValue() {
        return values.toArray(new String[0]);
    }

    @Override
    public void setValue(String[] value) {
        setValue(value, true);
    }

    @Override
    public void setValue(String[] value, boolean fireEvents) {
        // unselected items
        for (String v : values) {
            labelMap.get(v).removeStyleName(
                    resources.webuiCss().tagPanelSelectedItem());
        }

        values.clear();
        for (String v : value) {
            values.add(v);
            labelMap.get(v).addStyleName(
                    resources.webuiCss().tagPanelSelectedItem());
        }

        if (fireEvents) {
            ValueChangeEvent.fire(this, value);
        }
    }

}

//vim: ts=4 sw=4 expandtab