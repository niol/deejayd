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

import java.util.ArrayList;
import java.util.Collections;

public class DeejaydUtils {
	public static String formatTime(int time) {
		if (time > 3600) {
			// hours:minutes:seconds
			int hours = (int) time/3600;
			int mins = (int) (time%3600)/60;
			int secs = (int) time%60;
			return Integer.toString(hours)+":"+getDoubleDigit(mins)+":"
					+getDoubleDigit(secs);
		} else {
			// minutes:seconds
			int mins = (int) time/60;
			int secs = (int) time%60;
			return Integer.toString(mins)+":"+getDoubleDigit(secs);
		}
	}

	public static String formatTimeLong(int time, HasI18nMessages messages) {
		int[] dividors = new int[5];
		dividors[0] = 60;
		dividors[1] = 60;
		dividors[2] = 24;
		dividors[3] = 365;
		dividors[4] = 60;
		
		String[] divDescs = new String[5];
		divDescs[0] = "second";
		divDescs[1] = "minute";
		divDescs[2] = "hour";
		divDescs[3] = "day";
		divDescs[4] = "year";

		int unit = 0;
		ArrayList<String> timeStr = new ArrayList<String>();
		for (int i=0; i<5; i++) {
			int div = dividors[i];
			if (time < 1)
				break;
			if (div == 0) {
				unit = time;
				time = 0;
			} else {
				unit = (int) time % div;
				time = (int) time / div;
			}
			if (unit > 0) {
				String desc = "";
				if (divDescs[i] == "second")
					desc = messages.seconds(unit);
				else if (divDescs[i] == "minute")
					desc = messages.minutes(unit);
				else if (divDescs[i] == "hour")
					desc = messages.hours(unit);
				else if (divDescs[i] == "day")
					desc = messages.days(unit);
				else if (divDescs[i] == "year")
					desc = messages.years(unit);
				
				timeStr.add(desc);
			}
		}
		Collections.reverse(timeStr);
		if (timeStr.size() > 2)
			timeStr.remove(timeStr.size()-1);
		String result = "";
		for (String str : timeStr) {
			if (!result.equals(""))
				result += ", ";
			result += str;
		}
		return result;
	}

	/**
	 * get a double digit int from a single
	 * @param i
	 * @return
	 */
	private static String getDoubleDigit(int i) {
        String newI = null;
        switch (i) {
        case 0:
                newI = "00";
                break;
        case 1:
                newI = "01";
                break;
        case 2:
                newI = "02";
                break;
        case 3:
                newI = "03";
                break;
        case 4:
                newI = "04";
                break;
        case 5:
                newI = "05";
                break;
        case 6:
                newI = "06";
                break;
        case 7:
                newI = "07";
                break;
        case 8:
                newI = "08";
                break;
        case 9:
                newI = "09";
                break;
        default:
                newI = Integer.toString(i);
        }
        return newI;
	}
}

//vim: ts=4 sw=4 expandtab