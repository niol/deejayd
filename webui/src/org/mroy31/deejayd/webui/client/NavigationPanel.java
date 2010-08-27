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

package org.mroy31.deejayd.webui.client;

import org.mroy31.deejayd.common.events.StatusChangeEvent;
import org.mroy31.deejayd.common.events.StatusChangeHandler;
import org.mroy31.deejayd.common.rpc.DefaultRpcCallback;
import org.mroy31.deejayd.common.rpc.GenericRpcCallback;
import org.mroy31.deejayd.common.widgets.DeejaydUIWidget;
import org.mroy31.deejayd.webui.events.DragEnterEvent;
import org.mroy31.deejayd.webui.events.DragEnterHandler;
import org.mroy31.deejayd.webui.events.DragLeaveEvent;
import org.mroy31.deejayd.webui.events.DragLeaveHandler;
import org.mroy31.deejayd.webui.events.DragOverEvent;
import org.mroy31.deejayd.webui.events.DragOverHandler;
import org.mroy31.deejayd.webui.events.DropEvent;
import org.mroy31.deejayd.webui.events.DropHandler;
import org.mroy31.deejayd.webui.events.HasDropHandlers;
import org.mroy31.deejayd.webui.resources.WebuiResources;
import org.mroy31.deejayd.webui.widgets.LibraryManager;
import org.mroy31.deejayd.webui.widgets.LoadingWidget;
import org.mroy31.deejayd.webui.widgets.MagicPlsDialog;
import org.mroy31.deejayd.webui.widgets.NewPlsDialog;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.google.gwt.user.client.ui.Widget;

public class NavigationPanel extends WebuiPanel
        implements ClickHandler, StatusChangeHandler {

    private static NavigationPanelUiBinder uiBinder = GWT
            .create(NavigationPanelUiBinder.class);
    interface NavigationPanelUiBinder
            extends UiBinder<Widget, NavigationPanel> {}

    @UiField Button panelModeButton;
    @UiField VerticalPanel plsList;
    @UiField HorizontalPanel plsToolbar;
    @UiField Button plsStaticNewButton;
    @UiField Button plsMagicNewButton;
    @UiField(provided = true) final LibraryManager updateButton;
    @UiField(provided = true) final WebuiResources resources;

    private WebuiLayout ui;
    private String activeList = "";
    private String activePls = "";
    private int panelId = -1;
    private NewPlsDialog staticDg;
    private NewPlsDialog magicDg;
    private MagicPlsDialog magicEditDg = new MagicPlsDialog();

    private class PlsItem extends Composite implements HasDropHandlers {
        private String plsId;

        public PlsItem(JSONObject plsObj) {
            String type = plsObj.get("type").isString().stringValue();
            String name = plsObj.get("name").isString().stringValue();
            int id = (int) plsObj.get("id").isNumber().doubleValue();
            plsId = Integer.toString(id);

            HorizontalPanel item = new HorizontalPanel();
            item.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);
            item.setWidth("100%");

            HorizontalPanel desc = new HorizontalPanel();
            desc.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);
            desc.setSpacing(3);
            desc.setStyleName(resources.webuiCss().pointerCursor());

            ClickHandler handler = new PlsClickHandler(plsId);
            Image img = new Image(resources.playlist());
            if (type.equals("magic"))
                img = new Image(resources.magicPlaylist());
            img.addClickHandler(handler);
            desc.add(img);
            Label label = new Label(name);
            label.addClickHandler(handler);
            desc.add(label);
            item.add(desc);

            item.setHorizontalAlignment(HorizontalPanel.ALIGN_RIGHT);
            HorizontalPanel actionPanel = new HorizontalPanel();
            actionPanel.setSpacing(3);
            if (type.equals("magic")) {
                Button editButton = new Button();
                editButton.setStyleName(
                        resources.webuiCss().editButton()+" "+
                        resources.webuiCss().iconOnlyButton());
                editButton.addClickHandler(new PlsEditHandler(plsId, name));
                actionPanel.add(editButton);
            }
            Button removeButton = new Button();
            removeButton.setStyleName(
                    resources.webuiCss().clearButton()+" "+
                    resources.webuiCss().iconOnlyButton());
            removeButton.addClickHandler(new PlsRemoveHandler(plsId));
            actionPanel.add(removeButton);
            item.add(actionPanel);

            initWidget(item);
            if (type.equals("static")) {
                addDragEnterHandler(new DragEnterHandler() {
                    public void onDragEnter(DragEnterEvent event) {
                        addStyleName(ui.resources.webuiCss().mlRowOver());
                    }
                });
                addDragLeaveHandler(new DragLeaveHandler() {
                    public void onDragLeave(DragLeaveEvent event) {
                        removeStyleName(ui.resources.webuiCss().mlRowOver());
                    }
                });
                addDragOverHandler(new DragOverHandler() {
                    public void onDragOver(DragOverEvent event) {
                        event.preventDefault();
                    }
                });
                addDropHandler(new DropHandler() {
                    public void onDrop(DropEvent event) {
                        event.preventDefault();
                        removeStyleName(ui.resources.webuiCss().mlRowOver());
                        String[] data = event.dataTransfert()
                                             .getData().split("-");
                        ui.rpc.recPlsStaticAdd(plsId, new String[] {data[2]},
                                new DefaultRpcCallback(ui));
                    }
                });
            }
        }

        public String getPlsId() {
            return plsId;
        }

        public HandlerRegistration addDragEnterHandler(DragEnterHandler handler) {
            return addDomHandler(handler, DragEnterEvent.getType());
        }

        public HandlerRegistration addDragLeaveHandler(DragLeaveHandler handler) {
            return addDomHandler(handler, DragLeaveEvent.getType());
        }

        public HandlerRegistration addDragOverHandler(DragOverHandler handler) {
            return addDomHandler(handler, DragOverEvent.getType());
        }

        public HandlerRegistration addDropHandler(DropHandler handler) {
            return addDomHandler(handler, DropEvent.getType());
        }
    }

    /*
     * Specific rpc callbacks
     */
    private class PlsEraseCallback extends DefaultRpcCallback {
        public PlsEraseCallback(DeejaydUIWidget ui) { super(ui); }

        @Override
        public void onCorrectAnswer(JSONValue data) {
            updatePlsList();
        }
    }

    protected class PlsClickHandler implements ClickHandler {
        private String pls;
        public PlsClickHandler(String pls) { this.pls = pls; }

        public void onClick(ClickEvent event) {
            ui.rpc.panelModeSetActiveList("playlist", pls,
                    new DefaultRpcCallback(ui));
        }
    }

    protected class PlsEditHandler implements ClickHandler {
        private String plsId;
        private String plsName;
        public PlsEditHandler(String plsId, String plsName) {
            this.plsId = plsId;
            this.plsName = plsName;
        }

        public void onClick(ClickEvent event) {
            magicEditDg.load(plsName, plsId, true);
            magicEditDg.center();
        }
    }

    protected class PlsRemoveHandler implements ClickHandler {
        private String pls;
        public PlsRemoveHandler(String pls) { this.pls = pls; }

        public void onClick(ClickEvent event) {
            JSONArray sel = new JSONArray();
            sel.set(0, new JSONString(pls));
            boolean confirm = Window.confirm(
                    ui.i18nMessages.plsEraseConfirm(sel.size()));
            if (confirm) {
                if (activeList.equals("playlist") && pls.equals(activePls))
                    ui.rpc.panelModeSetActiveList("panel", "",
                            new DefaultRpcCallback(ui));
                ui.rpc.recPlsErase(sel, new PlsEraseCallback(ui));
            }
        }
    }

    /**
     * NavigationPanel Constructor
     * @param webui
     */
    public NavigationPanel(WebuiLayout webui) {
        super("panel");

        this.ui = webui;
        this.resources = webui.resources;
        this.updateButton = webui.audioLibrary;
        initWidget(uiBinder.createAndBindUi(this));

        panelModeButton.setText(ui.i18nConstants.panels());
        panelModeButton.addClickHandler(this);
        plsStaticNewButton.setText(ui.i18nConstants.staticPls());
        plsStaticNewButton.addClickHandler(this);
        plsMagicNewButton.setText(ui.i18nConstants.magicPls());
        plsMagicNewButton.addClickHandler(this);
        staticDg = new NewPlsDialog(new NewPlsDialog.PlsCommand() {
            public void execute(String plsName) {
                ui.rpc.recPlsCreate(plsName,"static",new GenericRpcCallback() {

                    @Override
                    public void setError(String error) {
                        ui.setError(error);
                    }

                    @Override
                    public void onCorrectAnswer(JSONValue data) {
                        updatePlsList();
                    }
                });
            }
        });
        magicDg = new NewPlsDialog(new NewPlsDialog.PlsCommand() {
            public void execute(String plsName) {
                ui.rpc.recPlsCreate(plsName, "magic", new GenericRpcCallback() {

                    @Override
                    public void setError(String error) {
                        ui.setError(error);
                    }

                    @Override
                    public void onCorrectAnswer(JSONValue data) {
                        // open dialog to set pls filter/property
                        JSONObject plsObj = data.isObject();
                        magicEditDg.load(
                                plsObj.get("name").isString().stringValue(),
                                plsObj.get("pl_id").isNumber().toString());
                        magicEditDg.center();
                        updatePlsList();
                    }
                });
            }
        });

        updatePlsList();
        ui.addStatusChangeHandler(this);
    }

    public void onClick(ClickEvent event) {
        Widget source = (Widget) event.getSource();
        if (source == panelModeButton) {
            if (activeList.equals("playlist")) {
                ui.rpc.panelModeSetActiveList("panel", "",
                        new DefaultRpcCallback(ui));
            }
        } else if (source == plsStaticNewButton) {
            staticDg.center();
        } else if (source == plsMagicNewButton) {
            magicDg.center();
        }
    }

    public void onStatusChange(StatusChangeEvent event) {
        int id = Integer.parseInt(event.getStatus().get("panel"));
        if (panelId != id) {
            updateActiveList();
            panelId = id;
        }
    }

    private void updateActiveList() {
        ui.rpc.panelModeActiveList(new GenericRpcCallback() {

            @Override
            public void setError(String error) {
                ui.setError(error);
            }

            @Override
            public void onCorrectAnswer(JSONValue data) {
                JSONObject obj = data.isObject();
                String type = obj.get("type").isString().stringValue();
                String pls = obj.get("value").isString().stringValue();
                if (!type.equals(activeList)) {
                    if (type.equals("panel")) {
                        // Clear pls selection
                        clearPlsSelection();
                        panelModeButton.addStyleName(
                                resources.webuiCss().bold());
                    } else {
                        panelModeButton.removeStyleName(
                                resources.webuiCss().bold());
                        setPlsSelection(pls);
                    }
                    activeList = type;
                } else if (type.equals("playlist") && !pls.equals(activePls)) {
                    // update playlist selection
                    setPlsSelection(pls);
                }
            }
        });
    }

    private void updatePlsList() {
        class PlsListCallback extends DefaultRpcCallback {
            public PlsListCallback(WebuiLayout ui) { super(ui); }

            @Override
            public void onCorrectAnswer(JSONValue data) {
                plsList.clear();
                JSONArray list = data.isObject().get("medias").isArray();

                for (int idx=0; idx<list.size(); idx++) {
                    JSONObject plsObj = list.get(idx).isObject();
                    plsList.add(new PlsItem(plsObj));
                }

                if (activeList.equals("playlist"))
                    setPlsSelection(activePls);
            }
        }

        plsList.clear();
        plsList.add(new LoadingWidget(ui.i18nConstants.loading(), resources));
        ui.rpc.recPlsList(new PlsListCallback(ui));
    }

    private void clearPlsSelection() {
        for (int idx=0; idx<plsList.getWidgetCount(); idx++) {
            try {
                PlsItem item = (PlsItem) plsList.getWidget(idx);
                item.removeStyleName(resources.webuiCss().currentItem());
            } catch (ClassCastException ex) {}
        }
    }

    private void setPlsSelection(String pls) {
        for (int idx=0; idx<plsList.getWidgetCount(); idx++) {
            PlsItem item = (PlsItem) plsList.getWidget(idx);
            item.removeStyleName(resources.webuiCss().currentItem());
            if (item.getPlsId().equals(pls))
                item.addStyleName(resources.webuiCss().currentItem());
        }
        activePls = pls;
    }
}

//vim: ts=4 sw=4 expandtab