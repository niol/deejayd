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

package org.mroy31.deejayd.webui.i18n;

import org.mroy31.deejayd.common.i18n.CommonI18nMessages;

import com.google.gwt.i18n.client.LocalizableResource.DefaultLocale;

@DefaultLocale("en")
public interface WebuiMessages extends CommonI18nMessages {

    @DefaultMessage("{0,number} Songs")
    @PluralText({"one", "1 Song"})
    String songsDesc(@PluralCount int number);

    @DefaultMessage("{0,number} Webradios")
    @PluralText({"one", "1 Webradio"})
    String webradiosDesc(@PluralCount int number);

    @DefaultMessage("Are you sure you want to erase these {0,number} playlists ?")
    @PluralText({"one", "Are you sure you want to erase this playlist ?"})
    String plsEraseConfirm(@PluralCount int number);

    @DefaultMessage("Update {0} library")
    String libUpdateButton(String libraryType);

    @DefaultMessage("Updating {0} library ...")
    String libUpdateLoading(String libraryType);

    @DefaultMessage("The {0} library has been updated.")
    String libUpdateMessage(String libraryType);
}

//vim: ts=4 sw=4 expandtab