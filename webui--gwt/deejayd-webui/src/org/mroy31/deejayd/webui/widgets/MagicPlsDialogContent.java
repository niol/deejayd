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

import org.mroy31.deejayd.common.rpc.BasicFilter;
import org.mroy31.deejayd.common.rpc.ComplexFilter;
import org.mroy31.deejayd.common.rpc.GenericRpcCallback;
import org.mroy31.deejayd.common.rpc.MediaFilter;
import org.mroy31.deejayd.webui.client.WebuiLayout;
import org.mroy31.deejayd.webui.resources.WebuiResources;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiFactory;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.ListBox;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.google.gwt.user.client.ui.Widget;

public class MagicPlsDialogContent extends Composite implements ClickHandler {
    private final WebuiLayout ui = WebuiLayout.getInstance();
    private String plsId;

    private static MagicPlsDialogContentUiBinder uiBinder = GWT
            .create(MagicPlsDialogContentUiBinder.class);

    interface MagicPlsDialogContentUiBinder
            extends UiBinder<VerticalPanel, MagicPlsDialogContent> {}

    private class RemoveFilterHandler implements ClickHandler {
        private Widget widget;

        public RemoveFilterHandler(Widget w) {
            widget = w;
        }

        @Override
        public void onClick(ClickEvent event) {
            rulesList.remove(widget);
        }
    }

    @UiField VerticalPanel mainPanel;
    @UiField Label rulesLabel;
    @UiField VerticalPanel rulesList;
    @UiField Button addRuleButton;;
    @UiField CheckBox useOrFilter;
    @UiField CheckBox limitPls;
    @UiField TextBox limitPlsNumber;
    @UiField Label limitPlsNumberLabel;
    @UiField Label limitSortLabel;
    @UiField ListBox limitSortOrder;
    @UiField CheckBox limitSortRevert;
    @UiField HorizontalPanel actionPanel;
    @UiField(provided = true) final WebuiResources resources;

    public MagicPlsDialogContent() {
        resources = ui.resources;
        initWidget(uiBinder.createAndBindUi(this));

        rulesLabel.setText(ui.i18nConstants.rules());
        mainPanel.setCellHorizontalAlignment(addRuleButton,
                HorizontalPanel.ALIGN_RIGHT);
        addRuleButton.setText(ui.i18nConstants.add());
        addRuleButton.addClickHandler(this);
        useOrFilter.setText(ui.i18nConstants.magicUseOrFilter());

        limitPls.setText(ui.i18nConstants.magicLimitPls());
        limitPls.addClickHandler(this);
        limitPlsNumberLabel.setText(ui.i18nConstants.songs());

        limitSortLabel.setText(ui.i18nConstants.magicLimitSort());
        setTagList(limitSortOrder);
        limitSortRevert.setText(ui.i18nConstants.magicLimitSortDirection());

        mainPanel.setCellHorizontalAlignment(actionPanel,
                HorizontalPanel.ALIGN_RIGHT);
    }

    @UiFactory HorizontalPanel makeHPanel() {
        HorizontalPanel panel = new HorizontalPanel();
        panel.setSpacing(3);
        panel.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);

        return panel;
    }

    @UiFactory VerticalPanel makeVPanel() {
        VerticalPanel panel = new VerticalPanel();
        panel.setSpacing(3);
        panel.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);

        return panel;
    }

    @Override
    public void onClick(ClickEvent event) {
        Widget source = (Widget) event.getSource();
        if (source == addRuleButton) {
            addFilter(null);
        } else if (source == limitPls) {
            setLimitEnabled(limitPls.getValue());
        }
    }

    private void setLimitEnabled(boolean enabled) {
        limitPlsNumber.setEnabled(enabled);
        limitSortOrder.setEnabled(enabled);
        limitSortRevert.setEnabled(enabled);
        if (!enabled) {
            limitPlsNumberLabel.addStyleName(resources.webuiCss().disabled());
            limitSortLabel.addStyleName(resources.webuiCss().disabled());
        } else {
            limitPlsNumberLabel.removeStyleName(
                    resources.webuiCss().disabled());
            limitSortLabel.removeStyleName(resources.webuiCss().disabled());
        }
    }

    public void addActionButton(Button b) {
        actionPanel.add(b);
    }

    public void load(String plsId, boolean loadFilter) {
        this.plsId = plsId;
        rulesList.clear();
        if (loadFilter) {
            // get filter list
            class GetFilterCallback extends GenericRpcCallback {
                public GetFilterCallback(WebuiLayout webui) { super(webui); }

                @Override
                public void onCorrectAnswer(JSONValue data) {
                    JSONObject filterObj = data.isObject()
                            .get("filter").isObject();
                    ComplexFilter filter = MediaFilter.parse(filterObj)
                            .isComplex();
                    if (filter != null) {
                        MediaFilter[] filters = filter.getFilters();
                        for (int idx=0; idx<filters.length; idx++)
                            addFilter(filters[idx]);
                    }
                }
            }
            ui.rpc.recPlsGet(this.plsId, new GetFilterCallback(ui));
        } else {
            addFilter(null);
        }

        // get properties
        class GetPropertiesCallback extends GenericRpcCallback {
            public GetPropertiesCallback(WebuiLayout webui) { super(webui); }

            @Override
            public void onCorrectAnswer(JSONValue data) {
                JSONObject properties = data.isObject();

                useOrFilter.setValue(properties.get("use-or-filter")
                        .isString().stringValue().equals("1"));
                limitPls.setValue(properties.get("use-limit")
                        .isString().stringValue().equals("1"));
                setLimitEnabled(limitPls.getValue());
                limitPlsNumber.setValue(properties.get("limit-value")
                        .isString().stringValue());
                selectListValue(limitSortOrder,
                        properties.get("limit-sort-value")
                        .isString().stringValue());
                limitSortRevert.setValue(properties.get("limit-sort-direction")
                        .isString().stringValue().equals("ascending"));
            }
        }
        ui.rpc.recPlsMagicGetProperties(plsId, new GetPropertiesCallback(ui));
    }

    public void save() {
        class NullCallback extends GenericRpcCallback {
            public NullCallback(WebuiLayout ui) { super(ui); }

            @Override
            public void onCorrectAnswer(JSONValue data) {}
        }
        NullCallback callback = new NullCallback(ui);

        // save properties
        ui.rpc.recPlsMagicSetProperty(plsId, "use-or-filter",
                formatCheckBoxValue(useOrFilter), callback);
        ui.rpc.recPlsMagicSetProperty(plsId, "use-limit",
                formatCheckBoxValue(limitPls), callback);
        if (limitPls.getValue()) {
            ui.rpc.recPlsMagicSetProperty(plsId, "limit-value",
                    limitPlsNumber.getValue(), callback);
            ui.rpc.recPlsMagicSetProperty(plsId, "limit-sort-value",
                    limitSortOrder.getValue(limitSortOrder.getSelectedIndex()),
                    callback);
            ui.rpc.recPlsMagicSetProperty(plsId, "limit-sort-direction",
                    formatCheckBoxValue(limitSortRevert), callback);
        }

        // save filter
        ui.rpc.recPlsMagicClearFilter(plsId, callback);
        for (int idx=0; idx<rulesList.getWidgetCount(); idx++) {
            HorizontalPanel panel = (HorizontalPanel) rulesList.getWidget(idx);
            ListBox tag = (ListBox) panel.getWidget(0);
            ListBox op = (ListBox) panel.getWidget(1);
            TextBox pattern = (TextBox) panel.getWidget(2);

            BasicFilter filter = new BasicFilter(
                    op.getValue(op.getSelectedIndex()),
                    tag.getValue(tag.getSelectedIndex()),
                    pattern.getValue());
            ui.rpc.recPlsMagicAddFilter(plsId, filter, callback);
        }
    }

    private String formatCheckBoxValue(CheckBox ck) {
        if (ck.getValue()) {
            return "1";
        } else {
            return "0";
        }
    }

    private void addFilter(MediaFilter filter) {
        HorizontalPanel panel = makeHPanel();

        ListBox tagList = new ListBox();
        setTagList(tagList);
        if (filter != null)
            selectListValue(tagList, filter.isBasic().getTag());
        panel.add(tagList);

        ListBox opList = makeOpList(
                tagList.getValue(tagList.getSelectedIndex()));
        if (filter != null)
            selectListValue(opList, filter.isBasic().getId());
        panel.add(opList);

        TextBox pattern = new TextBox();
        if (filter != null)
            pattern.setValue(filter.isBasic().getPattern());
        panel.add(pattern);

        Button removeButton = new Button(ui.i18nConstants.remove());
        removeButton.addClickHandler(new RemoveFilterHandler(panel));
        panel.add(removeButton);
        rulesList.add(panel);
    }

    private void setTagList(ListBox list) {
        list.addItem(ui.i18nConstants.title(), "title");
        list.addItem(ui.i18nConstants.artist(), "artist");
        list.addItem(ui.i18nConstants.album(), "album");
        list.addItem(ui.i18nConstants.genre(), "genre");
        list.addItem(ui.i18nConstants.rating(), "rating");
    }

    private void selectListValue(ListBox list, String tag) {
        for (int idx=0; idx<list.getItemCount(); idx++) {
            if (list.getValue(idx).equals(tag)) {
                list.setSelectedIndex(idx);
                break;
            }
        }
    }

    private ListBox makeOpList(String tag) {
        ListBox list = new ListBox();
        if (tag.equals("rating")) {
            list.addItem(">=", "higher");
            list.addItem("<=", "lower");
        } else {
            list.addItem(ui.i18nConstants.equals(), "equals");
            list.addItem(ui.i18nConstants.notEquals(), "notequals");
            list.addItem(ui.i18nConstants.contains(), "contains");
            list.addItem(ui.i18nConstants.notContains(), "notcontains");
        }

        return list;
    }
}

//vim: ts=4 sw=4 expandtab