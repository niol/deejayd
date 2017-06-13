// Deejayd, a media player daemon
// Copyright (C) 2007-2017 Mickael Royer <mickael.royer@gmail.com>
//                         Alexandre Rossi <alexandre.rossi@gmail.com>
//
// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License along
// with this program; if not, write to the Free Software Foundation, Inc.,
// 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import { Injectable } from '@angular/core';
import { Media, AudioMedia, VideoMedia } from '../models/media.model';

function num(n:number):string {
    if (n < 10) {
        return `0${n}`;
    }
    return `${n}`
}

@Injectable()
export class UtilsService {
    hasLastPos(media:Media) {
        return media != null && media.type == 'video' &&
            media.lastpos > 5*60 &&
            media.lastpos < media.length - 600;
    }

    formatTime(t:number):string {
        let seconds_left:number = t;

        let hours:number = Math.floor(seconds_left / 3600);
        seconds_left = seconds_left % 3600;

        let minutes = Math.floor(seconds_left / 60)
        seconds_left = seconds_left % 60

        let t_formatted:string = `${ num(minutes) }:${ num(seconds_left) }`;
        if (hours > 0) {
            t_formatted = `${ num(hours) }:` + t_formatted
        }
        return t_formatted
    }

    getMediaDesc(m:Media):string {
        if (m.type == "song") {
            let audio_m = m as AudioMedia;
            return ` ${audio_m.album} -- ${audio_m.artist} `;
        } else if (m.type == "video") {
            let video_m = m as VideoMedia;
            return ` ${video_m.videowidth}x${video_m.videoheight} `;
        }
        return "";
    }
}
