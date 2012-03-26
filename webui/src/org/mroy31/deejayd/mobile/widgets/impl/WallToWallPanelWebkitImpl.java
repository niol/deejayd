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

import org.mroy31.deejayd.mobile.events.AnimationEndHandler;
import org.mroy31.deejayd.mobile.events.DeejaydEventsUtils;
import org.mroy31.deejayd.mobile.widgets.WallToWallPanel;

public class WallToWallPanelWebkitImpl extends WallToWallPanelImpl {

    @Override
    public void showContextPanel(final WallToWallPanel panel) {
        DeejaydEventsUtils.addAnimationEndHandlerOnce(panel.getElement(),
                new AnimationEndHandler() {
                    public void onAnimationEnd() {
                        panel.getWall().getContents().setVisible(false);

                        panel.getContextPanel().removeStyleName(
                                ui.resources.mobileCss().slideup()+" "+
                                ui.resources.mobileCss().in());
                        panel.removeStyleName(ui.resources.mobileCss().slideup()
                                +" "+ui.resources.mobileCss().in()+" "+
                                ui.resources.mobileCss().reverse());
                }
            });
        panel.getContextPanel().setVisible(true);
        panel.getContextPanel().addStyleName(
                ui.resources.mobileCss().slideup()+" "+
                ui.resources.mobileCss().in());
        panel.addStyleName(ui.resources.mobileCss().slideup()+" "+
                ui.resources.mobileCss().in()+" "+
                ui.resources.mobileCss().reverse());
    }

    @Override
    public void hideContextPanel(final WallToWallPanel panel) {
    	DeejaydEventsUtils.addAnimationEndHandlerOnce(panel.getElement(),
                new AnimationEndHandler() {
                    public void onAnimationEnd() {
                        panel.getContextPanel().removeStyleName(
                                ui.resources.mobileCss().slideup()
                                +" "+ui.resources.mobileCss().out()+" "+
                                ui.resources.mobileCss().reverse());
                        panel.getContextPanel().setVisible(false);
                }
            });
        panel.getWall().getContents().setVisible(true);
        panel.getContextPanel().addStyleName(
                ui.resources.mobileCss().slideup()+" "+
                ui.resources.mobileCss().out()+" "+
                ui.resources.mobileCss().reverse());
    }

    @Override
    public void showParent(final WallToWallPanel current, final WallToWallPanel parent) {
        if (parent != null) {
        	DeejaydEventsUtils.addAnimationEndHandlerOnce(current.getElement(),
                new AnimationEndHandler() {
                    public void onAnimationEnd() {
                        current.removeStyleName(ui.resources.mobileCss().currentWall());
                        current.removeStyleName(ui.resources.mobileCss().slide()+" "+
                                ui.resources.mobileCss().out()+" "+
                                ui.resources.mobileCss().reverse());
                        parent.removeStyleName(ui.resources.mobileCss().slide()
                                +" "+ui.resources.mobileCss().in()+" "+
                                ui.resources.mobileCss().reverse());
                }
            });

            current.addStyleName(ui.resources.mobileCss().slide()+" "+
                    ui.resources.mobileCss().out()+" "+
                    ui.resources.mobileCss().reverse());
            parent.addStyleName(ui.resources.mobileCss().currentWall()+" "+
                    ui.resources.mobileCss().slide()+" "+
                    ui.resources.mobileCss().in()+" "+
                    ui.resources.mobileCss().reverse());
        }
    }

    @Override
    public void showChild(final WallToWallPanel current, final WallToWallPanel child) {
        if (child != null) {
        	DeejaydEventsUtils.addAnimationEndHandlerOnce(current.getElement(),
                new AnimationEndHandler() {
                    public void onAnimationEnd() {
                        current.removeStyleName(ui.resources.mobileCss().currentWall());
                        current.removeStyleName(ui.resources.mobileCss().slide()
                                +" "+ui.resources.mobileCss().out());
                        child.removeStyleName(ui.resources.mobileCss().slide()
                                +" "+ui.resources.mobileCss().in());
                }
            });

            current.addStyleName(ui.resources.mobileCss().slide()+" "+
                    ui.resources.mobileCss().out());
            child.addStyleName(ui.resources.mobileCss().currentWall()+" "+
                    ui.resources.mobileCss().slide()+" "+
                    ui.resources.mobileCss().in());
        }
    }

}

//vim: ts=4 sw=4 expandtab