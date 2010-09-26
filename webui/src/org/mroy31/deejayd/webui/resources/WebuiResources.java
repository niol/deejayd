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

package org.mroy31.deejayd.webui.resources;

import com.google.gwt.resources.client.ClientBundle;
import com.google.gwt.resources.client.CssResource;
import com.google.gwt.resources.client.ImageResource;
import com.google.gwt.resources.client.ImageResource.ImageOptions;
import com.google.gwt.resources.client.ImageResource.RepeatStyle;

public interface WebuiResources extends ClientBundle {

    interface WebuiCss extends CssResource {
        String refreshButton();
        String modeList();
        String bold();
        String italic();
        String fixedTable();
        String currentItem();
        String collapsed();
        String expanded();
        String blueToolbar();
        String blueToolbarBg();
        String toolbar();
        String oddRow();
        String iconAndTextButton();
        String iconOnlyButton();
        String pointerCursor();
        String disabled();
        String toolbarDescLabel();
        String textOverflow();

        /* message */
        String msgInformation();
        String msgWarning();
        String msgError();

        /* Medialist */
        String mlRowOver();

        /* player buttons */
        String playButton();
        String pauseButton();
        String stopButton();
        String nextButton();
        String previousButton();
        String playerButtonsBlock();

        /* playing title theme */
        String playingPanel();
        String playingTitle();
        String playingDesc();
        String playingTime();

        String toolbarButton();
        String modeToolbarButton();
        String shuffleButton();
        String clearButton();
        String removeButton();
        String gotoButton();
        String addButton();
        String saveButton();
        String searchButton();
        String editButton();
        String ratingButton();

        // Queue
        String queueButton();
        String queueDesc();
        String queueToolbarButton();

        // Webradio
        String wbCategorieItem();

        // Panel
        String plsPanel();
        String tagPanelItem();
        String tagPanelSelectedItem();

        // Playlist
        String rulesList();
        String plsRowOver();

        // Pager
        String goFirst();
        String goPrevious();
        String pagerDesc();
        String goNext();
        String goLast();
    }

    @Source("webui-css.css")
    WebuiCss webuiCss();

    @Source("play.png")
    ImageResource play();

    @Source("pause.png")
    ImageResource pause();

    @Source("stop.png")
    ImageResource stop();

    @Source("next.png")
    ImageResource next();

    @Source("previous.png")
    ImageResource previous();

    @Source("play-low.png")
    ImageResource playLow();

    @Source("playlist-new.png")
    ImageResource playlistNew();

    @Source("playlist.png")
    ImageResource playlist();

    @Source("shuffle.png")
    ImageResource shuffle();

    @Source("clear.png")
    ImageResource clear();

    @Source("medialist-play.png")
    ImageResource medialistPlay();

    ImageResource remove();

    @Source("goto.png")
    ImageResource goTo();

    ImageResource folder();

    ImageResource audio();

    ImageResource webradio();

    ImageResource video();

    ImageResource add();

    ImageResource save();

    @Source("toolbar-bg.png")
    @ImageOptions(repeatStyle=RepeatStyle.Horizontal)
    ImageResource toolbarBg();

    ImageResource search();

    @Source("magic-playlist.png")
    ImageResource magicPlaylist();

    ImageResource star();

    ImageResource loading();

    ImageResource slider();

    ImageResource sliderDisabled();

    ImageResource sliderSliding();

    ImageResource expanded();

    ImageResource collapsed();

    @ImageOptions(repeatStyle=RepeatStyle.Horizontal)
    ImageResource blueToolbarBg();

    ImageResource edit();

    @Source("dialog-error.png")
    ImageResource dialogError();

    @Source("dialog-information.png")
    ImageResource dialogInformation();

    @Source("dialog-warning.png")
    ImageResource dialogWarning();

    ImageResource arrowDown();

    ImageResource arrowDownDisabled();

    ImageResource arrowDownHover();

    ImageResource arrowDownPressed();

    ImageResource arrowUp();

    ImageResource arrowUpDisabled();

    ImageResource arrowUpHover();

    ImageResource arrowUpPressed();

    ImageResource drag();

    ImageResource goFirst();

    ImageResource goLast();

    ImageResource goNext();

    ImageResource goPrevious();
}

//vim: ts=4 sw=4 expandtab