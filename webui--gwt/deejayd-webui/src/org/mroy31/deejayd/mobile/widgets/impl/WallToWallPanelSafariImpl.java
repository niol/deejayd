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

package org.mroy31.deejayd.mobile.widgets.impl;

import org.mroy31.deejayd.mobile.events.AnimationEndEvent;
import org.mroy31.deejayd.mobile.events.AnimationEndHandler;
import org.mroy31.deejayd.mobile.widgets.ScrollToCommand;
import org.mroy31.deejayd.mobile.widgets.WallToWallPanel;

import com.google.gwt.event.shared.HandlerRegistration;
import com.google.gwt.user.client.DeferredCommand;

public class WallToWallPanelSafariImpl extends WallToWallPanelImpl {
    private HandlerRegistration animHandlerReg;

    @Override
    public void showParent(final WallToWallPanel current, final WallToWallPanel parent) {
        if (parent != null) {
            animHandlerReg = current.addAnimationEndHandler(
                new AnimationEndHandler() {
                    @Override
                    public void onAnimationEnd(AnimationEndEvent event) {
                        current.removeStyleName(ui.resources.mobileCss().currentWall());
                        current.removeStyleName(ui.resources.mobileCss().slide()+" "+
                                ui.resources.mobileCss().out()+" "+
                                ui.resources.mobileCss().reverse());
                        parent.removeStyleName(ui.resources.mobileCss().slide()
                                +" "+ui.resources.mobileCss().in()+" "+
                                ui.resources.mobileCss().reverse());

                        animHandlerReg.removeHandler();
                }
            });

            current.addStyleName(ui.resources.mobileCss().slide()+" "+
                    ui.resources.mobileCss().out()+" "+
                    ui.resources.mobileCss().reverse());
            parent.addStyleName(ui.resources.mobileCss().currentWall()+" "+
                    ui.resources.mobileCss().slide()+" "+
                    ui.resources.mobileCss().in()+" "+
                    ui.resources.mobileCss().reverse());

            DeferredCommand.addPause();
            DeferredCommand.addCommand(new ScrollToCommand(null));
        }
    }

    @Override
    public void showChild(final WallToWallPanel current, final WallToWallPanel child) {
        if (child != null) {
            animHandlerReg = current.addAnimationEndHandler(
                new AnimationEndHandler() {
                    @Override
                    public void onAnimationEnd(AnimationEndEvent event) {
                        current.removeStyleName(ui.resources.mobileCss().currentWall());
                        current.removeStyleName(ui.resources.mobileCss().slide()
                                +" "+ui.resources.mobileCss().out());
                        child.removeStyleName(ui.resources.mobileCss().slide()
                                +" "+ui.resources.mobileCss().in());


                        animHandlerReg.removeHandler();
                        animHandlerReg = null;
                }
            });

            current.addStyleName(ui.resources.mobileCss().slide()+" "+
                    ui.resources.mobileCss().out());
            child.addStyleName(ui.resources.mobileCss().currentWall()+" "+
                    ui.resources.mobileCss().slide()+" "+
                    ui.resources.mobileCss().in());

            DeferredCommand.addPause();
            DeferredCommand.addCommand(new ScrollToCommand(null));
        }
    }

}

//vim: ts=4 sw=4 expandtab