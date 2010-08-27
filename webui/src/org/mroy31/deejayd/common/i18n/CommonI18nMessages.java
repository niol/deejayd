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

package org.mroy31.deejayd.common.i18n;

import com.google.gwt.i18n.client.Messages;

public interface CommonI18nMessages extends Messages {

    @DefaultMessage("{0,number} seconds")
    @PluralText({"one", "1 second"})
    String seconds(@PluralCount int seconds);

    @DefaultMessage("{0,number} minutes")
    @PluralText({"one", "1 minute"})
    String minutes(@PluralCount int minutes);

    @DefaultMessage("{0,number} hours")
    @PluralText({"one", "1 hour"})
    String hours(@PluralCount int hours);

    @DefaultMessage("{0,number} days")
    @PluralText({"one", "1 day"})
    String days(@PluralCount int days);

    @DefaultMessage("{0,number} years")
    @PluralText({"one", "1 year"})
    String years(@PluralCount int years);
}

//vim: ts=4 sw=4 expandtab