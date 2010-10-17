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
import java.util.List;

import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.common.rpc.types.BasicFilter;
import org.mroy31.deejayd.common.rpc.types.ComplexFilter;
import org.mroy31.deejayd.common.rpc.types.MediaFilter;
import org.mroy31.deejayd.mobile.client.MobileLayout;
import org.mroy31.deejayd.mobile.widgets.ListPanel;
import org.mroy31.deejayd.mobile.widgets.LoadingWidget;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.user.client.Command;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.Label;


public class TagList extends Composite {
    private final MobileLayout ui = MobileLayout.getInstance();
    private ArrayList<String> tagList = new ArrayList<String>();
    private ComplexFilter filter = new ComplexFilter("and");
    private Command finishCmd;

    private Label title = new Label();
    private ListPanel list = new ListPanel();

    public TagList(Command cmd) {
        finishCmd = cmd;
        FlowPanel panel = new FlowPanel();
        panel.setWidth("100%");

        title.addStyleName(ui.resources.mobileCss().contextHeader());
        panel.add(title);
        panel.add(list);
        initWidget(panel);
        ui.rpc.panelModeGetTags(new AnswerHandler<List<String>>() {

            public void onAnswer(List<String> answer) {
                for (String tag : answer)
                    tagList.add(tag);
                // set first tag list
                setTagList(0);
            }
        });
    }

    public void setTagList(final int tagIdx) {
        final String tag = tagList.get(tagIdx);

        list.clear();
        list.add(new LoadingWidget());
        title.setText(getTagTitle(tag));

        ui.rpc.audioLibTagList(tag, filter, new AnswerHandler<List<String>>() {

            public void onAnswer(List<String> answer) {
                list.clear();
                Label allLabel = new Label(ui.i18nConst.all());
                allLabel.addStyleName(ui.resources.mobileCss().tagListItem());
                allLabel.addStyleName(ui.resources.mobileCss().italic());
                allLabel.addClickHandler(new ClickHandler() {
                    public void onClick(ClickEvent event) {
                        if (tagIdx < tagList.size()-1){
                            setTagList(tagIdx+1);
                        } else {
                            updatePanel();
                        }
                    }
                });
                list.add(allLabel);

                for (final String t : answer) {
                    Label tLabel = new Label(getTagValue(t));
                    tLabel.addStyleName(ui.resources.mobileCss().tagListItem());
                    tLabel.addClickHandler(new ClickHandler() {
                        public void onClick(ClickEvent event) {
                            filter.addFilter(new BasicFilter("equals", tag, t));
                            if (tagIdx < tagList.size()-1){
                                setTagList(tagIdx+1);
                            } else {
                                updatePanel();
                            }
                        }
                    });
                    list.add(tLabel);
                }
            }
        });
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

    private String getTagValue(String pattern) {
        if (pattern.equals("__various__"))
            return ui.i18nConst.variousArtist();
        else if (pattern.equals(""))
            return ui.i18nConst.unknown();
        return pattern;
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
