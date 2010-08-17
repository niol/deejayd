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
import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.user.client.Command;
import com.google.gwt.user.client.DeferredCommand;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Composite;
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
    final String TITLE_W = Integer.toString(Window.getClientWidth()-170)+"px";

    protected final MobileLayout ui = MobileLayout.getInstance();
    private WallToWallPanelImpl impl = GWT.create(WallToWallPanelImpl.class);

    private final WallToWallPanel parent;
    private WallToWallPanel child;

    private final WallPanel wall = new WallPanel();
    private final WallPanel context = new WallPanel();

    public WallToWallPanel(String title, WallToWallPanel par) {
        wall.addStyleName(ui.resources.mobileCss().wallPanel());
        wall.setTitle(title);
        this.parent = par;
        if (par != null) {
            par.setChild(this);
        }

        if (par != null) {
            wall.setLeftButton(par.getShortTitle(), new Command() {
                @Override
                public void execute() {
                    showParent();
                }
            });
        }

        // build context panel with a close button
        context.setVisible(false);
        context.addStyleName(ui.resources.mobileCss().contextPanel());
        context.setRightButton(ui.i18nConst.close(), new Command() {
            @Override
            public void execute() {
                setContextVisible(false);
            }
        }, false);
        wall.setContextPanel(context);

        initWidget(wall);
    }

    public WallPanel getContextPanel() {
        return context;
    }

    public WallPanel getWall() {
        return wall;
    }

    public void setContextWidget(String title, Widget w) {
        context.setTitle(title);
        context.setContents(w);
    }

    public void setContextVisible(boolean visible) {
        if (visible) {
            impl.showContextPanel(this);
        } else {
            impl.hideContextPanel(this);
        }
        DeferredCommand.addPause();
        DeferredCommand.addCommand(new ScrollToCommand(null));
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
        DeferredCommand.addPause();
        DeferredCommand.addCommand(new ScrollToCommand(null));
    }

    public void showChild() {
        impl.showChild(this, child);
        DeferredCommand.addPause();
        DeferredCommand.addCommand(new ScrollToCommand(null));
    }

    public void add(Widget w) {
        wall.setContents(w);
    }

    public void setWallTitle(String title) {
        setWallTitle(title, false);
    }

    public void setWallTitle(String text, boolean html) {
        wall.setTitle(text, html);
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
        wall.setRightButton(label, command, forward);
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