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
import com.google.gwt.dom.client.Element;
import com.google.gwt.dom.client.NativeEvent;
import com.google.gwt.user.cellview.client.CellList;
import com.google.gwt.user.client.Command;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.AbstractImagePrototype;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.HorizontalPanel;

public abstract class DefaultMode extends AbstractMode
        implements StatusChangeHandler {
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
        public void onBrowserEvent(Element parent, Media value, Object key,
                  NativeEvent event, ValueUpdater<Media> valueUpdater) {
            ui.rpc.goTo(value.getId(), new AnswerHandler<Boolean>() {
                public void onAnswer(Boolean answer) {
                    ui.update();
                    ui.getWallPanel("currentMode").showChild();
                }
            });
        }

        @Override
        public void render(Media value, Object key, StringBuilder sb) {
            if (value == null)
                return;

            sb.append("<table cellspacing='0' cellpadding='0' class='");
            sb.append(ui.resources.mobileCss().listItem()+"' ");
            sb.append("style='width=100%';>");
            sb.append("<tbody><tr>");

            sb.append("<td width='100%' style='vertical-align: middle;'>");
            sb.append("<div style='width: "+ITEM_WIDTH+"px;'>");
            String title = value.getTitle(); String desc = "";
            if (value.isSong()) {
                title += " ("+DeejaydUtils.formatTime(value.getIntAttr("length"))+")";
                if (value.hasAttr("artist"))
                    desc = value.getStrAttr("artist")+" - ";
                if (value.hasAttr("album"))
                    desc += "<b>"+value.getStrAttr("album")+"</b>";
            } else if (value.isVideo()) {
                title += " ("+DeejaydUtils.formatTime(value.getIntAttr("length"))+")";
                desc = value.getStrAttr("videowidth") + " - " +
                        value.getStrAttr("videoheight");
            } else if (value.isWebradio()) {
                // TODO
            }
            sb.append("<div class='"+ui.resources.mobileCss().mListTitle()+
                    "'>"+title+"</div>");
            sb.append("<div class='"+ui.resources.mobileCss().mListDesc()+
                    "'>"+desc+"</div>");
            sb.append("</div></td>");

            sb.append("<td>");
            sb.append(AbstractImagePrototype.create(ui.resources.chevron()).getHTML());
            sb.append("<td>");

            sb.append("</tr></tbody></table>");
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