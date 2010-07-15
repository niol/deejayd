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

package org.mroy31.deejayd.mobile.widgets;

import org.mroy31.deejayd.mobile.client.MobileLayout;
import org.mroy31.deejayd.mobile.events.AnimationEndEvent;
import org.mroy31.deejayd.mobile.events.AnimationEndHandler;
import org.mroy31.deejayd.mobile.events.HasAnimationHandlers;
import org.mroy31.deejayd.mobile.widgets.impl.WallToWallPanelImpl;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.user.client.Command;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.FlowPanel;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.Widget;

/**
 * This is the base class for all of the major UI panels. It is designed to fill
 * the full width of the client area and to have at most a single instance
 * attached to the DOM. The panel has a concept of having a parent or previous
 * panel that can be accessed by a "back" button, as well as a distinct "edit"
 * or alternate command that can be accessed by a second button in the title
 * bar.
 */
public abstract class WallToWallPanel extends Composite
        implements HasAnimationHandlers {
    protected final MobileLayout ui = MobileLayout.getInstance();
    private WallToWallPanelImpl impl = GWT.create(WallToWallPanelImpl.class);

    private final WallToWallPanel parent;
    private WallToWallPanel child;


    private final FlowPanel contents = new FlowPanel();
    private final HorizontalPanel header = new HorizontalPanel();
    private final UnsunkLabel titleLabel = new UnsunkLabel("");

    private Command editCommand;

    public WallToWallPanel(String title, WallToWallPanel par) {
        this.parent = par;
        if (par != null) {
            par.setChild(this);
        }

        // build header
        header.setVerticalAlignment(HorizontalPanel.ALIGN_MIDDLE);
        header.addStyleName(ui.resources.mobileCss().wallHeader());

        if (par != null) {
            Label l = new Label(par.getShortTitle());
            l.addStyleName(ui.resources.mobileCss().headerButton());
            l.addStyleName(ui.resources.mobileCss().headerBackButton());
            l.addClickHandler(new ClickHandler() {
                @Override
                public void onClick(ClickEvent event) {
                    showParent();
                }
            });
            header.add(l);
        }

        titleLabel.setText(title);
        titleLabel.setWidth(
                Integer.toString(Window.getClientWidth()-170)+"px");
        titleLabel.addStyleName(ui.resources.mobileCss().wallHeaderTitle());
        header.add(titleLabel);
        header.setCellWidth(titleLabel, "100%");
        header.setCellHorizontalAlignment(titleLabel,
                HorizontalPanel.ALIGN_CENTER);

        FlowPanel vp = new FlowPanel();
        vp.add(header);
        vp.add(contents);

        initWidget(vp);
    }

    public void setChild(WallToWallPanel ch) {
        this.child = ch;
        if (ch != null) {
            setRightCommand(ch.getShortTitle(), "", new Command() {
                @Override
                public void execute() {
                    showChild();
                }
            }, true);
        }
    }

    public void showParent() {
        impl.showParent(this, parent);
    }

    public void showChild() {
        impl.showChild(this, child);
    }

    public void add(Widget w) {
        contents.add(w);
    }

    public void clear() {
        contents.clear();
    }

    public void setWallTitle(String title) {
        setWallTitle(title, false);
    }

    public void setWallTitle(String text, boolean html) {
        if (html) {
            titleLabel.removeStyleName(
                    ui.resources.mobileCss().wallHeaderTitle());
            titleLabel.addStyleName(
                    ui.resources.mobileCss().wallHeaderHTMLTitle());
            titleLabel.setHTML(text);

        } else {
            titleLabel.removeStyleName(
                    ui.resources.mobileCss().wallHeaderHTMLTitle());
            titleLabel.addStyleName(ui.resources.mobileCss().wallHeaderTitle());
            titleLabel.setText(text);
        }
    }

    public void setRightCommand(String label, String title, Command command) {
        setRightCommand(label, title, command, false);
    }

    /**
     * Set the command to be executed by a right-justified button in the title
     * bar.
     *
     * @param label the label for the button
     * @param title the title or alt-text for the button
     * @param command the Command to execute when the button is pressed
     * @param forward use forward button icon.
     */
    public void setRightCommand(String label, String title,
            Command command, boolean forward) {
        editCommand = command;
        Label l = new Label(label);
        l.addStyleName(ui.resources.mobileCss().headerButton());
        if (forward) {
            l.addStyleName(ui.resources.mobileCss().headerForwardButton());
        }
        l.setTitle(title);
        l.addClickHandler(new ClickHandler() {

            @Override
            public void onClick(ClickEvent event) {
                editCommand.execute();
            }
        });
        header.add(l);
        header.setCellHorizontalAlignment(l, HorizontalPanel.ALIGN_RIGHT);
    }

    @Override
    public HandlerRegistration addAnimationEndHandler(
            AnimationEndHandler handler) {
        return addDomHandler(handler, AnimationEndEvent.getType());
    }

    /**
     * A short title to be used as the label of the back button.
     */
    protected abstract String getShortTitle();
}

//vim: ts=4 sw=4 expandtab