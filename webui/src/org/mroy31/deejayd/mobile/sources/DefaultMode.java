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
import org.mroy31.deejayd.common.events.StatusChangeHandler;
import org.mroy31.deejayd.common.provider.MediaListProvider;
import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.common.rpc.types.Media;
import org.mroy31.deejayd.common.widgets.DeejaydUtils;
import org.mroy31.deejayd.mobile.client.MobileLayout;
import org.mroy31.deejayd.mobile.client.SourcePanel;
import org.mroy31.deejayd.mobile.widgets.Pager;

import com.google.gwt.cell.client.AbstractCell;
import com.google.gwt.cell.client.ValueUpdater;
import com.google.gwt.core.client.GWT;
import com.google.gwt.dom.client.Element;
import com.google.gwt.dom.client.NativeEvent;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.safehtml.client.SafeHtmlTemplates;
import com.google.gwt.safehtml.shared.SafeHtml;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.cellview.client.CellList;
import com.google.gwt.user.client.Command;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.AbstractImagePrototype;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.HorizontalPanel;

public abstract class DefaultMode extends AbstractMode
        implements StatusChangeHandler {

    interface Template extends SafeHtmlTemplates {
        @Template("<table style=\"width=100%;\" cellspacing=\"0\" cellpadding=\"0\" class=\"{1}\"><tbody><tr>{0}</tr></tbody></table>")
        SafeHtml tbody(SafeHtml rowHtml, String classes);

        @Template("<td width=\"100%\" style=\"vertical-align: middle;\">{0}</td>")
        SafeHtml td(SafeHtml contents);

        @Template("<div style=\"width:{1};\">{0}</div>")
        SafeHtml div(SafeHtml contents, String width);
    }
    private static final Template TEMPLATE = GWT.create(Template.class);

    protected static MobileLayout ui = MobileLayout.getInstance();
    protected SourcePanel manager;
    protected String name;
    protected int PAGE_SIZE = 15;
    protected String ITEM_WIDTH = Integer.toString(Window.getClientWidth()-100);

    protected Pager mediaList;
    protected HorizontalPanel toolbar = new HorizontalPanel();
    protected Command hideCtxCmd = new Command() {
        public void execute() {
            manager.setContextVisible(false);
        }
    };

    private MediaListProvider provider;
    private AbstractCell<Media> cell = new AbstractCell<Media>(new String[] {"click"}) {

        @Override
        public void onBrowserEvent(Context context, Element parent, Media value,
                  NativeEvent event, ValueUpdater<Media> valueUpdater) {
            ui.rpc.goTo(value.getId(), new AnswerHandler<Boolean>() {
                public void onAnswer(Boolean answer) {
                    ui.update();
                    ui.getWallPanel("currentMode").showChild();
                }
            });
        }

        @Override
        public void render(Context context, Media value, SafeHtmlBuilder sb) {
            if (value == null)
                return;

            SafeHtmlBuilder tdBuilder = new SafeHtmlBuilder();
            String title = value.getTitle(); String desc = "";
            if (value.isSong()) {
                title += " ("+DeejaydUtils.formatTime(value.getIntAttr("length"))+")";
                if (value.hasAttr("artist"))
                    desc = value.getStrAttr("artist")+" - ";
                if (value.hasAttr("album"))
                    desc += value.getStrAttr("album");
            } else if (value.isVideo()) {
                title += " ("+DeejaydUtils.formatTime(value.getIntAttr("length"))+")";
                desc = value.getStrAttr("videowidth") + " - " +
                        value.getStrAttr("videoheight");
            } else if (value.isWebradio()) {
                if ("pls".equals(value.getStrAttr("url-type")))
                    desc = value.getStrAttr("url");
                else if ("urls".equals(value.getStrAttr("url-type"))) {
                    JSONArray urls = value.getArrayAttr("urls");
                    if (urls.size() == 1)
                        desc = urls.get(0).isString().stringValue();
                    else
                        desc=ui.i18nMsg.urlCount(urls.size());
                }
            }
            String titleClass = ui.resources.mobileCss().mListTitle();
            tdBuilder.appendHtmlConstant("<div class='"+titleClass+"'>")
                     .appendEscaped(title)
                     .appendHtmlConstant("</div>");
            String descClass = ui.resources.mobileCss().mListDesc();
            tdBuilder.appendHtmlConstant("<div class='"+descClass+"'>")
                     .appendEscaped(desc)
                     .appendHtmlConstant("</div>");

            SafeHtmlBuilder trBuilder = new SafeHtmlBuilder();
            trBuilder.append(TEMPLATE.td(TEMPLATE.div(tdBuilder.toSafeHtml(),
                    ITEM_WIDTH+"px")));
            trBuilder.appendHtmlConstant("<td>"+AbstractImagePrototype
                    .create(ui.resources.chevron()).getHTML()+"</td>");

            sb.append(TEMPLATE.tbody(trBuilder.toSafeHtml(),
                    ui.resources.mobileCss().listItem()));
        }
    };

    public DefaultMode(String name, SourcePanel manager) {
        this.manager = manager;
        this.name = name;
        this.provider = new MediaListProvider(ui, name);

        toolbar.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);
        toolbar.setSpacing(5);
        initToolbar(toolbar);

        FlowPanel panel = new FlowPanel();
        panel.add(toolbar);

        // medialist
        CellList<Media> mediaList = new CellList<Media>(cell);
        mediaList.setStyleName(ui.resources.mobileCss().listPanel());
        mediaList.setPageSize(PAGE_SIZE);
        provider.getDataProvider().addDataDisplay(mediaList);
        // pager
        Pager pager = new Pager();
        pager.setDisplay(mediaList);

        panel.add(pager);
        panel.add(mediaList);
        initWidget(panel);

        ui.addStatusChangeHandler(this);
    }

    public void onStatusChange(StatusChangeEvent event) {
        provider.onStatusChange(event);
    }

    abstract public void initToolbar(HorizontalPanel toolbar);
}

//vim: ts=4 sw=4 expandtab