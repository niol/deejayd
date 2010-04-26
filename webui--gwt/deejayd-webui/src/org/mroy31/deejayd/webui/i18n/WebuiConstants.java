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
    String newPlsDgCaption();

    @DefaultStringValue("Cancel")
    String cancel();

    @DefaultStringValue("Source:")
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

    @DefaultStringValue("Categories")
    String wbCategories();

    @DefaultStringValue("Go to current webradio")
    String wbGoCurrent();

    @DefaultStringValue("Loading categories list...")
    String wbLoadingCategories();

    @DefaultStringValue("audio")
    String audio();

    @DefaultStringValue("video")
    String video();

    @DefaultStringValue("Loading ...")
    String loading();

    @DefaultStringValue("Queue")
    String queue();

    @DefaultStringValue("Panels")
    String panels();

    @DefaultStringValue("Static Playlist")
    String staticPls();

    @DefaultStringValue("Magic Playlist")
    String magicPls();

    @DefaultStringValue("Add song if at least one filter match")
    String magicUseOrFilter();

    @DefaultStringValue("Limit to ")
    String magicLimitPls();

    @DefaultStringValue("When sort by ")
    String magicLimitSort();

    @DefaultStringValue("Revert sort direction")
    String magicLimitSortDirection();

    @DefaultStringValue("Rules")
    String rules();

    @DefaultStringValue("Songs")
    String songs();

    @DefaultStringValue("Equals")
    String equals();

    @DefaultStringValue("Not equals")
    String notEquals();

    @DefaultStringValue("Contains")
    String contains();

    @DefaultStringValue("Not contains")
    String notContains();

    @DefaultStringValue("Choose All")
    String chooseAll();

    @DefaultStringValue("Unknown")
    String unknown();

    @DefaultStringValue("Close")
    String close();

    @DefaultStringValue("Width")
    String width();

    @DefaultStringValue("Height")
    String height();

    @DefaultStringValue("Subtitle")
    String subtitle();

    @DefaultStringValue("Go to current video")
    String goCurrentVideo();

    @DefaultStringValue("Video Directories")
    String videoDirectories();

    @DefaultStringValue("Audio/Video Offset")
    String avOffset();

    @DefaultStringValue("Zoom")
    String zoom();

    @DefaultStringValue("Aspect Ratio")
    String aspectRatio();

    @DefaultStringValue("Audio Channels")
    String audioChannels();

    @DefaultStringValue("Subtitle Channels")
    String subChannels();

    @DefaultStringValue("Subtitle Offset")
    String subOffset();

    @DefaultStringValue("Reload")
    String reload();

    @DefaultStringValue("Dvd")
    String dvd();

    @DefaultStringValue("Panel Mode")
    String panel();

    @DefaultStringValue("Webradio")
    String webradio();

    @DefaultStringValue("Video")
    String videoMode();
}

// vim: ts=4 sw=4 expandtab