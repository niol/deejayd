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

package org.mroy31.deejayd.mobile.i18n;

import com.google.gwt.i18n.client.Constants;
import com.google.gwt.i18n.client.LocalizableResource.DefaultLocale;

@DefaultLocale("en")
public interface MobileConstants extends Constants {

    @DefaultStringValue("Mode List")
    String modeList();

    @DefaultStringValue("Refresh")
    String refresh();

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

    @DefaultStringValue("Loading ...")
    String loading();

    @DefaultStringValue("Queue")
    String queue();

    @DefaultStringValue("Close")
    String close();

    @DefaultStringValue("Dvd")
    String dvd();

    @DefaultStringValue("Playlist")
    String playlist();

    @DefaultStringValue("Panel Mode")
    String panel();

    @DefaultStringValue("Webradio")
    String webradio();

    @DefaultStringValue("Video")
    String videoMode();

    @DefaultStringValue("Player")
    String player();

    @DefaultStringValue("No Playing Media")
    String noPlayingMedia();

    @DefaultStringValue("List")
    String list();

    @DefaultStringValue("Title")
    String title();

    @DefaultStringValue("Options")
    String options();

    @DefaultStringValue("Play Order")
    String playOrder();

    @DefaultStringValue("save")
    String save();

    @DefaultStringValue("All")
    String all();

    @DefaultStringValue("Genre")
    String genre();

    @DefaultStringValue("Artist")
    String artist();

    @DefaultStringValue("Album")
    String album();

    @DefaultStringValue("Various artists")
    String variousArtist();

    @DefaultStringValue("Update panels")
    String updatePanel();

    @DefaultStringValue("Add Files")
    String addFiles();

    @DefaultStringValue("Add")
    String add();

    @DefaultStringValue("Files has been added to the playlist")
    String plsAddMsg();

    @DefaultStringValue("Unknown")
    String unknown();

    @DefaultStringValue("Select")
    String select();
}

// vim: ts=4 sw=4 expandtab