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
import org.mroy31.deejayd.mobile.resources.MobileResources;
import org.mroy31.deejayd.mobile.widgets.Pager;

import com.google.gwt.cell.client.AbstractCell;
import com.google.gwt.cell.client.ValueUpdater;
import com.google.gwt.core.client.GWT;
import com.google.gwt.dom.client.Element;
import com.google.gwt.dom.client.NativeEvent;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.cellview.client.Column;
import com.google.gwt.user.cellview.client.DeejaydCellTable;
import com.google.gwt.user.client.Command;
import com.google.gwt.user.client.ui.AbstractImagePrototype;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Widget;

public abstract class DefaultMode extends AbstractMode
        implements StatusChangeHandler {
	
	private static DefaultModeUiBinder uiBinder = GWT
            .create(DefaultModeUiBinder.class);
    interface DefaultModeUiBinder extends UiBinder<Widget, DefaultMode> {}
    
    @UiField HorizontalPanel toolbar;
    @UiField FlowPanel mediaListPanel;
    @UiField Pager pager;
    @UiField(provided = true) final MobileResources resources = ui.resources;

    protected static MobileLayout ui = MobileLayout.getInstance();
    protected SourcePanel manager;
    protected String name;
    protected int PAGE_SIZE = 15;

    protected Command hideCtxCmd = new Command() {
        public void execute() {
            manager.setContextVisible(false);
        }
    };

    private MediaListProvider provider;
    private AbstractCell<Media> cCell = new AbstractCell<Media>(new String[] {"click"}) {
    	
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
    		sb.append(AbstractImagePrototype.
        			create(ui.resources.chevron()).getSafeHtml());
    	}
    };
    private AbstractCell<Media> titleCell = new AbstractCell<Media>(new String[] {"click"}) {

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

            String title = value.getTitle(); String desc = "";
            String titleClass = ui.resources.mobileCss().mListTitle();
            String descClass = ui.resources.mobileCss().mListDesc();
            
            if (value.isSong()) {
                title += " ("+DeejaydUtils.formatTime(value.getIntAttr("length"))+")";
                if (value.hasAttr("artist"))
                    desc = value.getStrAttr("artist")+" - ";
                if (value.hasAttr("album"))
                    desc += value.getStrAttr("album");
            } else if (value.isVideo()) {
                title += " ("+DeejaydUtils.formatTime(value.getIntAttr("length"))+")";
                desc = value.getStrAttr("videowidth") + "x" +
                        value.getStrAttr("videoheight");
                boolean hasSub = !value.getStrAttr("external_subtitle").equals("");
                desc += " -- ";
                if (hasSub)
                	desc += ui.i18nConst.withSubtitle();
                else
                	desc += ui.i18nConst.withoutSubtitle();
                
                if (value.getIntAttr("playcount") == 0) {
                	title = "*"+title;
            	}
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
            
            sb.appendHtmlConstant("<div class='"+titleClass+"'>")
                     .appendEscaped(title)
                     .appendHtmlConstant("</div>");           
            sb.appendHtmlConstant("<div class='"+descClass+"'>")
                     .appendEscaped(desc)
                     .appendHtmlConstant("</div>");
        }
    };

    public DefaultMode(String name, SourcePanel manager) {
    	initWidget(uiBinder.createAndBindUi(this));
    	
        this.manager = manager;
        this.name = name;
        this.provider = new MediaListProvider(ui, name);

        toolbar.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);
        toolbar.setSpacing(5);
        initToolbar(toolbar);

        // medialist
        DeejaydCellTable<Media> mediaList = new DeejaydCellTable<Media>(PAGE_SIZE, ui.resources);
        mediaList.addColumn(new Column<Media, Media>(titleCell) {

			@Override
			public Media getValue(Media object) {
				return object;
			}
		});
        mediaList.addColumn(new Column<Media, Media>(cCell) {

			@Override
			public Media getValue(Media object) {
				return object;
			}
		});
        mediaList.setColumnWidth(1, "30px");   
        
        provider.getDataProvider().addDataDisplay(mediaList);
        mediaListPanel.add(mediaList);
        // pager
        pager.setDisplay(mediaList);

        ui.addStatusChangeHandler(this);
    }

    public void onStatusChange(StatusChangeEvent event) {
        provider.onStatusChange(event);
    }

    abstract public void initToolbar(HorizontalPanel toolbar);
}

//vim: ts=4 sw=4 expandtab