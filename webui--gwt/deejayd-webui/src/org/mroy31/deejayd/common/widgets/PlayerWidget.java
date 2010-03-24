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

package org.mroy31.deejayd.common.widgets;

import org.mroy31.deejayd.common.rpc.GenericRpcCallback;

import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.ui.Composite;

public abstract class PlayerWidget extends Composite {

	/*
	 * RPC callbacks
	 */
	protected class CoverCallback extends GenericRpcCallback {
		public CoverCallback(DeejaydUIWidget ui) {super(ui);}
		public void onCorrectAnswer(JSONValue data) {
			JSONString cover = data.isObject().get("cover").isString();
			updateCover(cover);
		}
	}

	protected class CurrentCallback extends GenericRpcCallback {
		public CurrentCallback(DeejaydUIWidget ui) {super(ui);}
		public void onCorrectAnswer(JSONValue data) {
			JSONObject media = data.isObject().get("medias")
								   .isArray().get(0).isObject();
			formatCurrentTitle(media);
		}
	}

	abstract protected void updateCover(JSONString cover);
	abstract protected void formatCurrentTitle(JSONObject media);
}

//vim: ts=4 sw=4 expandtab