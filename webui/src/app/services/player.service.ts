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
import { MatSnackBar } from '@angular/material';
import { Subject, Observable, BehaviorSubject } from "rxjs/Rx";
import { DjdClientService } from './djd-client.service';
import { Media } from '../models/media.model';

export interface PlayerStatus {
    state: string,
    volume: number,
    time?:string,
    current?:string
}

@Injectable()
export class PlayerService {
  private playerStatus:BehaviorSubject<PlayerStatus> = new BehaviorSubject<PlayerStatus>({
    state: "stop",
    volume: 0,
  });
  public playerStatus$ = this.playerStatus.asObservable();

  private playingMedia:BehaviorSubject<Media> = new BehaviorSubject<Media>(null);
  public playingMedia$ = this.playingMedia.asObservable();

  constructor(private client:DjdClientService, private snackbar: MatSnackBar) {
    client.isConnected$.subscribe((connected:boolean) => {
      if (connected) {
        this.updateStatus();
        this.updateCurrent();
        this.setSubscriptions();
      }
    });
  }

  displayError(error: string) {
      let snackBarRef = this.snackbar.open(error, "Close", {
          duration: 5000
      });
      snackBarRef.onAction().subscribe(() => {
          snackBarRef.dismiss();
      });
  }

  setSubscriptions():void {
    this.client.subscribe("player.status", (signal:Object) => {
        this.updateStatus();
    });
    this.client.subscribe("player.current", (signal:Object) => {
        this.updateCurrent();
    });
  }

  updateStatus():void {
    this.client.sendCommand("player.getStatus", []).subscribe((answer: any) => {
      this.playerStatus.next(answer as PlayerStatus);
    }, this.displayError);
  }

  updateCurrent():void {
    this.client.sendCommand("player.getPlaying", []).subscribe((answer: any) => {
      this.playingMedia.next(answer as Media);
    }, this.displayError);
  }

  playToggle():void {
    this.client.sendSimpleCmd("player.playToggle", []);
  }

  stop():void {
    this.client.sendSimpleCmd("player.stop", []);
  }

  next():void {
    this.client.sendSimpleCmd("player.next", []);
  }

  previous():void {
    this.client.sendSimpleCmd("player.previous", []);
  }

  setVolume(volume: number):void {
    this.client.sendSimpleCmd("player.setVolume", [volume]);
  }

  setVolumeRelative(step: number):void {
    this.client.sendSimpleCmd("player.setVolume", [step, true]);
  }

  seek(pos: number, relative:boolean = false):void {
    this.client.sendSimpleCmd("player.seek", [pos, relative]);
  }

  goTo(id: number, type:string, source:string, pos:number = 0):void {
    if (pos == 0) {
      this.client.sendSimpleCmd("player.goTo", [id, type, source]);
    } else {
      this.client.sendCommand("player.goTo", [id, type, source])
                 .subscribe((answer:any) => {
        this.seek(pos);
      }, this.displayError);
    }
  }

  playFolder(f_id:number, source:string):void {
    this.client.sendCommand(`${source}.loadFolders`, [[f_id], false])
               .subscribe((answer:any) => {
      this.goTo(0, "pos", source);
    }, this.displayError)
  }

  playMedia(m_id:number, source:string):void {
    this.client.sendCommand(`${source}.loadMedias`, [[m_id], false])
               .subscribe((answer:any) => {
      this.goTo(0, "pos", source);
    }, this.displayError)
  }

  resumeMedia(m_id:number, source:string, pos:number):void {
    this.client.sendCommand(`${source}.loadMedias`, [[m_id], false])
               .subscribe((answer:any) => {
      this.goTo(0, "pos", source, pos);
    }, this.displayError);
  }

  getVideoOptions():Observable<any> {
    return this.client.sendCommand("player.getAvailableVideoOptions", []);
  }

  setVideoOption(name:string, value:string|number):void {
    this.client.sendSimpleCmd("player.setVideoOption", [name, value]);
  }
}
