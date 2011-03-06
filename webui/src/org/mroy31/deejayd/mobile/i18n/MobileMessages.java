/* Deejayd, a media player daemon
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

import org.mroy31.deejayd.common.i18n.CommonI18nMessages;

import com.google.gwt.i18n.client.LocalizableResource.DefaultLocale;

@DefaultLocale("en")
public interface MobileMessages extends CommonI18nMessages {

    @DefaultMessage("{0,number} Playlists")
    @AlternateMessage({"one", "1 Playlist"})
    String plsCount(@PluralCount int number);

    @DefaultMessage("{0,number} Urls")
    @AlternateMessage({"one", "1 Url"})
    String urlCount(@PluralCount int number);

    @DefaultMessage("{0,number} Songs")
    @AlternateMessage({"one", "1 Song"})
    String songsDesc(@PluralCount int number);

    @DefaultMessage("{0,number} Webradios")
    @AlternateMessage({"one", "1 Webradio"})
    String webradiosDesc(@PluralCount int number);

    @DefaultMessage("{0,number} Videos")
    @AlternateMessage({"one", "1 Video"})
    String videosDesc(@PluralCount int number);

    @DefaultMessage("Are you sure you want to erase these {0,number} playlists ?")
    @AlternateMessage({"one", "Are you sure you want to erase this playlist ?"})
    String plsEraseConfirm(@PluralCount int number);

    @DefaultMessage("{0,number} Tracks")
    @AlternateMessage({"one", "1 Track"})
    String tracksDesc(@PluralCount int number);

    @DefaultMessage("Track {0,number}")
    String dvdTrack(int idx);

    @DefaultMessage("Chapter {0,number}")
    String dvdChapter(int idx);

    @DefaultMessage("{0,number}/{1,number} items loaded")
    @AlternateMessage({"one", "1/{1,number} item loaded"})
    String itemLoadedDesc(@PluralCount int number, int total);
}

//vim: ts=4 sw=4 expandtab