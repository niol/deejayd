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

import org.mroy31.deejayd.common.rpc.callbacks.AnswerHandler;
import org.mroy31.deejayd.common.rpc.types.Media;
import org.mroy31.deejayd.webui.cellview.DeejaydSelModel;
import org.mroy31.deejayd.webui.client.WebuiLayout;

import com.google.gwt.core.client.Scheduler;
import com.google.gwt.event.dom.client.BlurEvent;
import com.google.gwt.event.dom.client.BlurHandler;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.user.client.DOM;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.PopupPanel;
import com.google.gwt.user.client.ui.VerticalPanel;

public class RatingButton extends Composite {
    private final WebuiLayout ui;
    private final DeejaydSelModel<Media> selModel;

    private class RatingMenu extends PopupPanel {
        private class Handler implements ClickHandler {
            private final int value;

            public Handler(int value) {
                this.value = value;
            }

            public void onClick(ClickEvent event) {
                ArrayList<String> sel = new ArrayList<String>();
                for (Media m : selModel.getSelectedSet())
                    sel.add(m.getStrAttr("media_id"));
                if (!sel.isEmpty())
                    ui.rpc.setRating(sel, value, new AnswerHandler<Boolean>() {

                        public void onAnswer(Boolean answer) {
                            ui.update();
                            menu.hide();
                        }
                    });
            }
        }

        public RatingMenu() {
            VerticalPanel panel = new VerticalPanel();
            for (int value=0; value<5; value++) {
                HorizontalPanel entry = new HorizontalPanel();
                for (int i=0; i<4; i++) {
                    Image img = new Image(ui.resources.star());
                    if (i >= value) {
                        DOM.setStyleAttribute(img.getElement(), "opacity", "0.4");
                    }
                    entry.add(img);
                }
                entry.addDomHandler(new Handler(value), ClickEvent.getType());
                panel.add(entry);
            }
            setWidget(panel);
        }
    }
    private final RatingMenu menu;

    public RatingButton(WebuiLayout webui, DeejaydSelModel<Media> selModel) {
        this.ui = webui;
        this.selModel = selModel;
        this.menu = new RatingMenu();

        Button button = new Button(ui.i18nConstants.rating());
        button.setStyleName(ui.resources.webuiCss().modeToolbarButton()+" "+
                ui.resources.webuiCss().ratingButton());
        button.addClickHandler(new ClickHandler() {

            public void onClick(ClickEvent event) {
                if (menu.isShowing()) {
                    menu.hide();
                } else {
                    menu.setPopupPositionAndShow(
                            new PopupPanel.PositionCallback() {
                                public void setPosition(int offsetWidth,
                                        int offsetHeight) {
                                    int left = getAbsoluteLeft();
                                    int top = getAbsoluteTop()-
                                            menu.getOffsetHeight();
                                    menu.setPopupPosition(left, top);
                          }
                    });
                }
            }
        });
        button.addDomHandler(new BlurHandler() {

            public void onBlur(BlurEvent event) {
                // Be sure we hide menu after CLickEvent was handle
                Scheduler.get().scheduleDeferred(new Scheduler.ScheduledCommand() {

                    public void execute() {
                        menu.hide();
                    }
                });
            }
        }, BlurEvent.getType());

        initWidget(button);
    }
}

//vim: ts=4 sw=4 expandtab