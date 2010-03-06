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

package org.mroy31.deejayd.webui.i18n;

import com.google.gwt.i18n.client.Constants;

public interface WebuiConstants extends Constants {

    @DefaultStringValue("Play")
    String play();

    @DefaultStringValue("Refresh")
    String refresh();

    @DefaultStringValue("Title")
    String title();

    @DefaultStringValue("Artist")
    String artist();

    @DefaultStringValue("Album")
    String album();

    @DefaultStringValue("Genre")
    String genre();

    @DefaultStringValue("Length")
    String length();

    @DefaultStringValue("Rating")
    String rating();

    @DefaultStringValue("Shuffle")
    String shuffle();

    @DefaultStringValue("Clear")
    String clear();

    @DefaultStringValue("Remove")
    String remove();

    @DefaultStringValue("In order")
    String inOrder();

    @DefaultStringValue("One media")
    String oneMedia();

    @DefaultStringValue("Random")
    String random();

    @DefaultStringValue("Weighted Random")
    String weightedRandom();

    @DefaultStringValue("Repeat")
    String repeat();

    @DefaultStringValue("Directory")
    String directory();

    @DefaultStringValue("Search")
    String search();

    @DefaultStringValue("Update Audio Library")
    String updateAudioLibrary();

    @DefaultStringValue("Update Video Library")
    String updateVideoLibrary();

    @DefaultStringValue("Playlist")
    String playlist();

    @DefaultStringValue("Playlists")
    String playlists();

    @DefaultStringValue("All")
    String all();

    @DefaultStringValue("Add")
    String add();

    @DefaultStringValue("Add in Queue")
    String addQueue();

    @DefaultStringValue("Go to current song")
    String goCurrentSong();

    @DefaultStringValue("Url")
    String url();

    @DefaultStringValue("Clear search")
    String clearSearch();

    @DefaultStringValue("The playlist has been saved.")
    String plsSaveMsg();

    @DefaultStringValue("Save")
    String save();

    @DefaultStringValue("Enter playlist name")
    String saveDgCaption();

    @DefaultStringValue("Cancel")
    String cancel();

    @DefaultStringValue("Current Webradio Source:")
    String wbCurrentSource();

    @DefaultStringValue("Add a Webradio")
    String wbAdd();

    @DefaultStringValue("Webradio Name:")
    String wbName();

    @DefaultStringValue("Webradio Url:")
    String wbUrl();

    @DefaultStringValue("Recorded Webradios")
    String wbLocalSource();

    @DefaultStringValue("Shoutcast Webradios")
    String wbShoutcastSource();
}

// vim: ts=4 sw=4 expandtab