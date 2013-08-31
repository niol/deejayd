/*
 * Deejayd, a media player daemon
 * Copyright (C) 2007-2012 Mickael Royer <mickael.royer@gmail.com>
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

package org.mroy31.deejayd.mobile.resources;

import com.google.gwt.resources.client.CssResource;
import com.google.gwt.resources.client.DataResource;
import com.google.gwt.resources.client.ImageResource;
import com.google.gwt.resources.client.ImageResource.ImageOptions;
import com.google.gwt.resources.client.ImageResource.RepeatStyle;
import com.google.gwt.user.cellview.client.DeejaydCellTable;

public interface MobileResources extends DeejaydCellTable.Resources {

    interface MobileCss extends CssResource {
        String mainBody();
        String center();
        String italic();
        String button();

        String msgPanel();
        String error();
        String information();

        String currentWall();
        String wallPanel();
        String wallHeader();
        String wallHeaderTitle();
        String wallHeaderHTMLTitle();

        String headerButton();
        String headerBackButton();
        String headerForwardButton();

        String modeListDesc();
        String modeListItem();
        String contextPanel();
        String contextHeader();

        /*
         * Slider
         */
        String slider();
        String sliderHandle();
        
        /*
         * FlipSwitch
         */
        String flipSwitch();
        String flipSwitchElt();
        String flipSwitchOnElt();
        String flipSwitchOffElt();
        
        /*
         * SpinnerValue
         */
        String spinnerValue();
        
        /*
         * Player buttons
         */
        String playerPanel();
        String playerButtonPanel();
        String playerButton();
        String play();
        String stop();
        String pause();
        String next();
        String previous();
        /*
         * Cover
         */
        String coverImg();
        /*
         * Volume control
         */
        String volPanel();

        /*
         * Time SeekBar
         */
        String optionPanel();
        String seekBar();
        String seekBarDesc();
        String goFirst();
        String goPrevious();
        String goNext();
        String goLast();

        /*
         * Medialist
         */
        String chevron();
        String mListPager();
        String mListTitle();
        String mListDesc();
        String dvdTrack();
        
        /*
         * Toolbar buttons
         */
        String option();
        String add();
        String clear();
        String shuffle();

        /*
         * effects
         */
        String slide();
        String slideup();
        String in();
        String out();
        String reverse();
    }

    @Source("MobileCellTable.css")
    DeejaydCellTable.Style cellTableStyle();

    @Source("MobileCss.css")
    MobileCss mobileCss();

    ImageResource loading();

    ImageResource next();

    ImageResource pause();

    ImageResource play();

    ImageResource previous();

    ImageResource stop();

    @ImageOptions(repeatStyle=RepeatStyle.Both)
    ImageResource toolbar();

    @Source("go-next.png")
    ImageResource goNext();

    @Source("back_button.png")
    DataResource backButton();

    @Source("forward_button.png")
    DataResource forwardButton();

    @Source("button.png")
    DataResource button();

    @Source("vol-down.png")
    ImageResource volDown();

    @Source("vol-up.png")
    ImageResource volUp();

    @Source("missing-cover.png")
    ImageResource missingCover();

    @Source("go-previous.png")
    ImageResource goPrevious();

    @Source("go-last.png")
    ImageResource goLast();

    @Source("go-first.png")
    ImageResource goFirst();

    ImageResource chevron();

    ImageResource options();

    ImageResource add();

    ImageResource folder();

    ImageResource clear();

    ImageResource refresh();

    @Source("audio-file.png")
    ImageResource audioFile();

	ImageResource downArrow();

	ImageResource leftArrow();

	ImageResource rightArrow();

	ImageResource upArrow();
}

//vim: ts=4 sw=4 expandtab