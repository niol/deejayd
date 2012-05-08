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

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.ListIterator;

import org.mroy31.deejayd.common.provider.MediaTagProvider;
import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.common.rpc.types.BasicFilter;
import org.mroy31.deejayd.common.rpc.types.ComplexFilter;
import org.mroy31.deejayd.common.rpc.types.MediaFilter;
import org.mroy31.deejayd.mobile.client.MobileLayout;
import org.mroy31.deejayd.mobile.resources.MobileResources;
import org.mroy31.deejayd.mobile.widgets.Pager;

import com.google.gwt.cell.client.AbstractCell;
import com.google.gwt.cell.client.ValueUpdater;
import com.google.gwt.core.client.GWT;
import com.google.gwt.dom.client.Element;
import com.google.gwt.dom.client.NativeEvent;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.uibinder.client.UiBinder;
import com.google.gwt.uibinder.client.UiField;
import com.google.gwt.user.cellview.client.CellList;
import com.google.gwt.user.cellview.client.HasKeyboardSelectionPolicy.KeyboardSelectionPolicy;
import com.google.gwt.user.client.Command;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.Widget;


public class TagList extends Composite {
	private static TagListUiBinder uiBinder = GWT
            .create(TagListUiBinder.class);
    interface TagListUiBinder extends UiBinder<Widget, TagList> {}
	
    private final MobileLayout ui = MobileLayout.getInstance();
    
    private ArrayList<String> avTags = new ArrayList<String>();
    private ListIterator<String> avTagsIterator;
    
    private HashMap<String, BasicFilter> tagFilters = new HashMap<String, BasicFilter>();
    private ComplexFilter filter = new ComplexFilter("and");
    private Command finishCmd;

    private MediaTagProvider provider;
    private int PAGE_SIZE = 25;
    
    @UiField Label headerTitle;
    @UiField Pager pager;
    @UiField FlowPanel tagListPanel;
    @UiField FlowPanel leftButtonBox;
    @UiField(provided = true) final MobileResources resources = ui.resources;
    
    private AbstractCell<MediaTagProvider.MediaTag> cell = new AbstractCell<MediaTagProvider.MediaTag>(new String[] {"click"}) {

        @Override
        public void onBrowserEvent(Context context, Element parent, 
        		MediaTagProvider.MediaTag value, NativeEvent event, 
        		ValueUpdater<MediaTagProvider.MediaTag> valueUpdater) {
        	// update related basic filter
        	if (!value.getValue().equals("__all__")) {
	        	BasicFilter f = tagFilters.get(value.getType());
	        	f.setPattern(value.getValue());
	        	
	        	filter.addFilter(f);
        	}
        	if (avTagsIterator.hasNext()) {
        		updateTagList(avTagsIterator.next());
        	} else {
        		updatePanel();
        	}
        }

        @Override
        public void render(Context context, MediaTagProvider.MediaTag value, SafeHtmlBuilder sb) {
        	sb.appendEscaped(value.getName());
        }
    };

    public TagList(Command cmd) {
    	initWidget(uiBinder.createAndBindUi(this));
        finishCmd = cmd;
        this.provider = new MediaTagProvider(ui);
        
        // medialist
        CellList<MediaTagProvider.MediaTag> tagList = 
        		new CellList<MediaTagProvider.MediaTag>(cell, ui.cellListRessources);
        tagList.setKeyboardSelectionPolicy(KeyboardSelectionPolicy.DISABLED);
        tagList.setPageSize(PAGE_SIZE);
        provider.getDataProvider().addDataDisplay(tagList);
        tagListPanel.add(tagList);
        // pager
        pager.setDisplay(tagList);
        ui.rpc.panelModeGetTags(new AnswerHandler<List<String>>() {

            public void onAnswer(List<String> answer) {
                for (String tag : answer) {
                	avTags.add(tag);
                	tagFilters.put(tag, new BasicFilter("equals", tag, ""));
                }
                avTagsIterator = avTags.listIterator();
                // set first tag list
                updateTagList(avTagsIterator.next());
            }
        });
    }

    public void updateTagList(String tag) {
    	setHeader(tag);
        provider.updateList(tag, filter);
    }

    private void setHeader(String tag) {
    	headerTitle.setText(getTagTitle(tag));
    	leftButtonBox.clear();
    	if (avTagsIterator.previousIndex() > 0) {   		
    		final String prevTag = avTags.get(avTagsIterator.previousIndex()-1);
    	    
    		Label l = new Label(getTagTitle(prevTag));
	        l.addStyleName(resources.mobileCss().button());
	        l.addStyleName(resources.mobileCss().headerButton());
	        l.addStyleName(resources.mobileCss().headerBackButton());
	        l.addClickHandler(new ClickHandler() {
	            public void onClick(ClickEvent event) {
	            	avTagsIterator.previous();
	            	
	            	// remove last filter
	            	filter.removeFilter(tagFilters.get(prevTag));	            	
	                updateTagList(prevTag);
	            }
	        });
	        leftButtonBox.add(l);
    	}
    }
    
    private void updatePanel() {
        class Callback implements AnswerHandler<Boolean> {
            int idx = 0;

            public Callback(int idx) {
                this.idx = idx;
            }

            public void onAnswer(Boolean answer) {
                if (idx < filter.getFilters().length) {
                    ArrayList<String> values = new ArrayList<String>();

                    MediaFilter f = filter.getFilters()[idx];
                    values.add(f.isBasic().getPattern());
                    ui.rpc.panelModeSetFilter(f.isBasic().getTag(),
                            values, new Callback(idx+1));
                } else {
                    ui.rpc.panelModeSetActiveList("panel", "", null);
                    finishCmd.execute();
                }
            }
        }

        ui.rpc.panelModeClearAll(new Callback(0));
    }

    private String getTagTitle(String tag) {
        if (tag.equals("genre"))
            return ui.i18nConst.genre();
        else if (tag.equals("album"))
            return ui.i18nConst.album();
        else if (tag.equals("artist") || tag.equals("various_artist"))
            return ui.i18nConst.artist();
        return "";
    }
}

//vim: ts=4 sw=4 expandtab
