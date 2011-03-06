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

package org.mroy31.deejayd.webui.cellview.columns;

import com.google.gwt.cell.client.AbstractCell;
import com.google.gwt.cell.client.ValueUpdater;
import com.google.gwt.dom.client.Element;
import com.google.gwt.dom.client.InputElement;
import com.google.gwt.dom.client.NativeEvent;
import com.google.gwt.safehtml.shared.SafeHtml;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.safehtml.shared.SafeHtmlUtils;

public class CkSelCell extends AbstractCell<Boolean> {

    /**
     * An html string representation of a checked input box.
     */
     private SafeHtml INPUT_CHECKED = SafeHtmlUtils.fromSafeConstant("<input type=\"checkbox\" tabindex=\"-1\" checked/>");

     /**
      * An html string representation of an unchecked input box.
      */
     private SafeHtml INPUT_UNCHECKED = SafeHtmlUtils.fromSafeConstant("<input type=\"checkbox\" tabindex=\"-1\"/>");

     public CkSelCell() {
         super("change");
     }

     @Override
     public void render(Context context, Boolean value, SafeHtmlBuilder sb) {
         if (value)
             sb.append(INPUT_CHECKED);
         else
             sb.append(INPUT_UNCHECKED);
     }

     @Override
     public void onBrowserEvent(Context context, Element parent, Boolean value,
              NativeEvent event, ValueUpdater<Boolean> valueUpdater) {
         InputElement input = parent.getFirstChild().cast();
         Boolean isChecked = input.isChecked();

         if (valueUpdater != null) {
           valueUpdater.update(isChecked);
         }
     }

}

//vim: ts=4 sw=4 expandtab