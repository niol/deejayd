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

import java.util.HashMap;

import org.mroy31.deejayd.common.events.StatsChangeEvent;
import org.mroy31.deejayd.common.events.StatusChangeEvent;
import org.mroy31.deejayd.common.events.StatusChangeHandler;
import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.common.rpc.callbacks.RpcHandler;
import org.mroy31.deejayd.common.widgets.DeejaydUIWidget;
import org.mroy31.deejayd.common.widgets.DeejaydUtils;
import org.mroy31.deejayd.webui.events.DragLeaveEvent;
import org.mroy31.deejayd.webui.events.DragOverEvent;
import org.mroy31.deejayd.webui.events.DropEvent;
import org.mroy31.deejayd.webui.i18n.WebuiConstants;
import org.mroy31.deejayd.webui.i18n.WebuiMessages;
import org.mroy31.deejayd.webui.medialist.MediaList;
import org.mroy31.deejayd.webui.medialist.MediaListDropCommand;
import org.mroy31.deejayd.webui.medialist.SongRenderer;
import org.mroy31.deejayd.webui.resources.WebuiResources;
import org.mroy31.deejayd.webui.widgets.LibraryManager;
import org.mroy31.deejayd.webui.widgets.WebuiSplitLayoutPanel;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ChangeEvent;
import com.google.gwt.event.dom.client.ChangeHandler;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiFactory;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.client.Command;
import com.google.gwt.user.client.DOM;
import com.google.gwt.user.client.DeferredCommand;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.DockLayoutPanel;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.ListBox;
import com.google.gwt.user.client.ui.Widget;

public class WebuiLayout extends DeejaydUIWidget
        implements ClickHandler, StatusChangeHandler {
    static private WebuiLayout instance;
    public LibraryManager audioLibrary;
    public LibraryManager videoLibrary;
    private boolean queueOpen = false;
    private int queueId = -1;
    private int queueOverRow = -1;


    public WebuiConstants i18nConstants = GWT.create(WebuiConstants.class);
    public WebuiMessages i18nMessages = GWT.create(WebuiMessages.class);

    private static LayoutUiBinder uiBinder = GWT.create(LayoutUiBinder.class);
    interface LayoutUiBinder extends UiBinder<Widget, WebuiLayout> {}

    WebuiSplitLayoutPanel modePanel;
    WebuiModeManager modeManager;
    WebuiPanelManager panelManager;
    MediaList queueList;

    private class WebuiMessage extends Message {

        public WebuiMessage(String message, String type) {
            super(message, type);
        }

        @Override
        protected Widget buildWidget(String message, String type) {
            FlowPanel panel = new FlowPanel();
            DOM.setStyleAttribute(panel.getElement(), "position", "fixed");
            DOM.setStyleAttribute(panel.getElement(), "zIndex", "1");
            DOM.setStyleAttribute(panel.getElement(), "top", "0px");
            DOM.setStyleAttribute(panel.getElement(), "width", "300px");
            DOM.setStyleAttribute(panel.getElement(), "padding", "7px");
            // set message position based on window width
            int left = (Window.getClientWidth() - 300)/2;
            DOM.setStyleAttribute(panel.getElement(), "left",
                    Integer.toString(Math.max(0, left))+"px");

            HorizontalPanel msgPanel = new HorizontalPanel();
            msgPanel.setSpacing(4);
            msgPanel.setWidth("100%");
            msgPanel.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);
            Image typeImg = new Image();
            if (type.equals("error")) {
                panel.addStyleName(resources.webuiCss().msgError());
                typeImg.setResource(resources.dialogError());
            } else if (type.equals("warning")) {
                panel.addStyleName(resources.webuiCss().msgWarning());
                typeImg.setResource(resources.dialogWarning());
            } else if (type.equals("information")) {
                panel.addStyleName(resources.webuiCss().msgInformation());
                typeImg.setResource(resources.dialogInformation());
            }
            msgPanel.add(typeImg);
            msgPanel.add(new Label(message));
            msgPanel.setHorizontalAlignment(HorizontalPanel.ALIGN_RIGHT);
            msgPanel.add(new Button(i18nConstants.close(), new ClickHandler() {
                public void onClick(ClickEvent event) {
                    removeFromParent();
                }
            }));

            panel.add(msgPanel);
            return panel;
        }
    }

    @UiField FlowPanel topPanel;
    @UiField PlayerUI playerUI;
    @UiField Button refreshButton;
    @UiField ListBox modeList;
    @UiField DockLayoutPanel mainPanel;
    @UiField HorizontalPanel bottomBar;
    @UiField Image loading;
    @UiField HorizontalPanel queueBar;
    @UiField Button queueButton;
    @UiField Image queueState;
    @UiField Label queueDesc;
    @UiField HorizontalPanel queueToolbar;
    @UiField CheckBox queueRandom;
    @UiField Button queueRemove;
    @UiField Button queueClear;
    @UiField Label queueLoading;
    @UiField(provided = true) public final WebuiResources resources;

    static public WebuiLayout getInstance() {
        if (instance == null)
            instance = new WebuiLayout();
        return instance;
    }

    public WebuiLayout() {
        // load ressources
        resources = GWT.create(WebuiResources.class);
        resources.webuiCss().ensureInjected();

        initWidget(uiBinder.createAndBindUi(this));
        loading.setResource(resources.loading());
        bottomBar.setCellHorizontalAlignment(loading,
                HorizontalPanel.ALIGN_RIGHT);
        refreshButton.addClickHandler(this);
        refreshButton.setText(i18nConstants.refresh());

        modeList.addChangeHandler(new ChangeHandler() {
            public void onChange(ChangeEvent event) {
                String mode = modeList.getValue(modeList.getSelectedIndex());
                rpc.setMode(mode, null);
            }
        });

        // Init queue
        queueButton.setText(i18nConstants.queue());
        queueButton.addClickHandler(this);
        queueRandom.setText(i18nConstants.random());
        queueRandom.addValueChangeHandler(new ValueChangeHandler<Boolean>() {
            public void onValueChange(ValueChangeEvent<Boolean> event) {
                String playorder = event.getValue() ? "random" : "inorder";
                instance.rpc.setOption("queue", "playorder", playorder, null);
            }
        });
        queueClear.setText(i18nConstants.clear());
        queueClear.addClickHandler(this);
        queueRemove.setText(i18nConstants.remove());
        queueRemove.addClickHandler(this);
        DOM.setStyleAttribute(queueLoading.getElement(), "paddingLeft", "10px");
        queueList = new MediaList(this, "queue");
        queueList.setOption(true,new SongRenderer(this, "queue", queueLoading));
        queueList.addDragDropCommand(new MediaListDropCommand() {

            public void onDrop(DropEvent event, int row) {
                String[] data = event.dataTransfert().getData().split("-");
                if (data[0].equals("queue")) {
                    rpc.queueMove(new String[] {data[1]}, row, null);
                } else {
                    JSONArray sel = new JSONArray();
                    sel.set(0, new JSONString(data[2]));
                    rpc.queueLoadIds(sel, row, null);
                }
                if (queueOverRow != -1) {
                    queueList.getRowFormatter().removeStyleName(
                            queueOverRow,
                            resources.webuiCss().mlRowOver());
                    queueOverRow = -1;
                }
            }

            public void onDragOver(DragOverEvent event, int row) {
                if (row != queueOverRow) {
                    if (queueOverRow != -1) {
                        queueList.getRowFormatter().removeStyleName(
                            queueOverRow, resources.webuiCss().mlRowOver());
                    }
                    if (row != -1 )
                        queueList.getRowFormatter().addStyleName(row,
                                resources.webuiCss().mlRowOver());
                    queueOverRow = row;
                }
            }

            public void onDragLeave(DragLeaveEvent event) {
                if (queueOverRow != -1) {
                    queueList.getRowFormatter().removeStyleName(
                            queueOverRow, resources.webuiCss().mlRowOver());
                    queueOverRow = -1;
                }
            }
        });


        // Init Mode Panel
        panelManager = new WebuiPanelManager(this);
        modeManager = new WebuiModeManager(this);

        modePanel = new WebuiSplitLayoutPanel();
        modePanel.addSouth(queueList, 0);
        modePanel.addWest(panelManager, 300);
        modePanel.add(modeManager);
        mainPanel.add(modePanel);
        modePanel.setSplitPosition(queueList, 0, false);

        addStatusChangeHandler(this);
        DeferredCommand.addCommand(new Command() {
            public void execute() {
                load();
            }
        });
    }

    @UiFactory HorizontalPanel makeHPanel() {
        HorizontalPanel panel = new HorizontalPanel();
        panel.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);

        return panel;
    }

    public void onClick(ClickEvent event) {
        Widget source = (Widget) event.getSource();
        if (source == refreshButton) {
            update();
        } else if (source == queueButton) {
            if (queueOpen) {
                queueButton.removeStyleName(resources.webuiCss().expanded());
                queueButton.addStyleName(resources.webuiCss().collapsed());
                modePanel.setSplitPosition(queueList, 0, true);
            } else {
                queueButton.removeStyleName(resources.webuiCss().collapsed());
                queueButton.addStyleName(resources.webuiCss().expanded());
                modePanel.setSplitPosition(queueList, 100, true);
            }
            queueToolbar.setVisible(!queueOpen);
            queueOpen = !queueOpen;
        } else if (source == queueRemove) {
            rpc.queueRemove(queueList.getSelection(), null);
        } else if (source == queueClear) {
            rpc.queueClear();
        }
    }

    @UiFactory PlayerUI makePlayerUI() {
        return new PlayerUI(this);
    }

    @Override
    public void setMessage(String message, String type) {
        topPanel.add(new WebuiMessage(message, type));
    }

    private void load() {
        this.rpc.addRpcHandler(new RpcHandler() {

            public void onRpcStop() {
                loading.setVisible(false);
            }

            public void onRpcStart() {
                loading.setVisible(true);
            }

            public void onRpcError(String error) {
                setMessage(error, "error");
            }
        });

        // init audio library
        HashMap<String, String> messages = new HashMap<String, String>();
        messages.put("button", i18nMessages.libUpdateButton(
                i18nConstants.audio()));
        messages.put("confirmation", i18nMessages.libUpdateMessage(
                i18nConstants.audio()));
        messages.put("loading", i18nMessages.libUpdateLoading(
                i18nConstants.audio()));
        audioLibrary = new LibraryManager(this, "audio", messages);

        // load mode list
        rpc.getModeList(new AnswerHandler<HashMap<String,String>>() {

            public void onAnswer(HashMap<String, String> answer) {
                for (String key : answer.keySet()) {
                    boolean av = Boolean.valueOf(answer.get(key));
                    if (av) {
                        modeList.addItem(getSourceTitle(key), key);
                        if (key.equals("video")) {
                            // init video library
                            HashMap<String, String> msg =
                                new HashMap<String, String>();
                            msg.put("button", i18nMessages.libUpdateButton(
                                    i18nConstants.video()));
                            msg.put("confirmation", i18nMessages
                                    .libUpdateMessage(i18nConstants.video()));
                            msg.put("loading", i18nMessages.libUpdateLoading(
                                    i18nConstants.video()));
                            videoLibrary = new LibraryManager(
                                    WebuiLayout.getInstance(), "video", msg);
                        }
                    }
                }
                update();
            }
        });
    }

    @Override
    public void update() {
        super.update();

        this.rpc.getStats(new AnswerHandler<HashMap<String,String>>() {

            public void onAnswer(HashMap<String, String> stats) {
                fireEvent(new StatsChangeEvent(stats));
            }
        });
    }

    private String getSourceTitle(String source) {
        if (source.equals("panel")) {
            return i18nConstants.panel();
        } else if (source.equals("playlist")) {
            return i18nConstants.playlist();
        } else if (source.equals("webradio")) {
            return i18nConstants.webradio();
        } else if (source.equals("video")) {
            return i18nConstants.videoMode();
        } else if (source.equals("dvd")) {
            return i18nConstants.dvd();
        }
        return "";
    }

    public void onStatusChange(StatusChangeEvent event) {
        HashMap<String, String> status = event.getStatus();

        // select current mode
        String currentMode = status.get("mode");
        String mode = modeList.getValue(modeList.getSelectedIndex());
        if (!currentMode.equals(mode)) {
            for (int idx=0; idx<modeList.getItemCount(); idx ++) {
                if (currentMode.equals(modeList.getValue(idx))) {
                    modeList.setSelectedIndex(idx);
                    break;
                }
            }
        }

        // update queue medialist
        int id = Integer.parseInt(status.get("queue"));
        if (queueId != id) {
            queueList.update();
            // update desc
            int lg = Integer.parseInt(status.get("queuelength"));
            int tmlg = Integer.parseInt(status.get("queuetimelength"));
            if (lg == 0) {
                queueDesc.setText(i18nMessages.songsDesc(lg));
            } else {
                String desc = DeejaydUtils.formatTimeLong(tmlg,
                        i18nMessages);
                queueDesc.setText(i18nMessages.songsDesc(lg)+" ("+
                desc+")");
            }

            queueId = id;
        }
        // update queue state
        queueRandom.setValue(
                status.get("queueplayorder").equals("random"), false);
        if (!status.get("state").equals("stop")) {
            String current = status.get("current");
            String[] currentArray = current.split(":");
            if (currentArray[2].equals("queue")) {
                if (status.get("state").equals("play")) {
                    queueState.setResource(resources.play());
                } else {
                    queueState.setResource(resources.pause());
                }
            }
        } else {
            queueState.setResource(resources.stop());
        }
    }
}

//vim: ts=4 sw=4 expandtab