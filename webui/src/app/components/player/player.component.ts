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

import { Component } from '@angular/core';
import { OnInit } from '@angular/core';
import { MatSliderChange } from '@angular/material';
import { Timer } from '../../models/timer.model';
import { Media } from '../../models/media.model';
import { PlayerService, PlayerStatus } from '../../services/player.service';
import { UtilsService } from '../../services/utils.service';


@Component({
  selector: 'djd-player',
  template: `
  <div fxLayout='column' id="djd-player-toolbar">
    <djd-seekbar fxFlex="30px"
                 *ngIf="!seekbarMiniHidden"
                 style="width: 100%; opacity:0.8;"></djd-seekbar>
    <djd-volume fxFlex="30px"
                *ngIf="!volumeMiniHidden"
                style="width: 100%; opacity:0.8;"></djd-volume>

    <div fxFlex="85px" 
         fxLayout='row'
         fxLayout.lt-md='column'>
        <div fxLayoutAlign="center center" 
             fxFlex="1 1 270px"
             fxFlex.lt-md="1 1 100%">
            <div>
                <button mat-icon-button (click)="player.seek(-10, true)">
                    <mat-icon>replay_10</mat-icon>
                </button>
                <button mat-icon-button (click)=player.previous()>
                    <mat-icon>skip_previous</mat-icon>
                </button>
                <button mat-icon-button (click)=player.playToggle()>
                    <mat-icon *ngIf="!isPlaying">play_arrow</mat-icon>
                    <mat-icon *ngIf="isPlaying">pause</mat-icon>
                </button>
                <button mat-icon-button (click)=player.stop()>
                    <mat-icon>stop</mat-icon>
                </button>
                <button mat-icon-button (click)=player.next()>
                    <mat-icon>skip_next</mat-icon>
                </button>
                <button mat-icon-button (click)="player.seek(30, true)">
                    <mat-icon>forward_30</mat-icon>
                </button>
                <button mat-icon-button
                        fxHide [fxShow.lt-md]="true"
                        #vMiniButton
                        (click)="toggleVolumeMenu()">
                    <mat-icon>volume_up</mat-icon>
                </button>
            </div>
        </div>
        <div fxFlex="1 1 100%"
             fxLayout="column"
             fxLayout.lt-md='row'
             fxLayoutAlign="center center">
            <span class="djd-current-media">
                <ng-container *ngIf="currentMedia != null; else noMedia">{{ currentMedia.title }}</ng-container>
                <ng-template #noMedia i18n>No playing media</ng-template>
            </span>
            <button mat-button
                    *ngIf="currentMedia != null"
                    fxHide [fxShow.lt-md]="true"
                    (click)="toggleSeekbar()">
                {{ utils.formatTime(currentMedia.length) }}
            </button>

            <djd-seekbar fxFlex
                         fxShow [fxHide.lt-md]="true"
                         style="width: 100%"></djd-seekbar>
        </div>
        <djd-volume fxFlex="2 2 200px"
                    fxShow [fxHide.lt-md]="true"></djd-volume>
    </div>
  </div>
    `
})
export class PlayerComponent implements OnInit {
  public isPlaying:boolean = false;
  public currentMedia:Media = null;
  public volume:number = 0;
  public volumeMiniHidden:boolean = true;
  public seekbarMiniHidden:boolean = true;

  constructor(public player: PlayerService, private utils: UtilsService) { }

  ngOnInit(): void {
    this.player.playerStatus$.subscribe((status:PlayerStatus) => {
      this.isPlaying = status.state == "play";
      this.volume = status.volume;
    });
    this.player.playingMedia$.subscribe((media: Media) => {
        this.currentMedia = media;
    });
  }

  log(event:any) {
      console.log(event.value);
  }

  toggleVolumeMenu() {
      this.volumeMiniHidden = !this.volumeMiniHidden;
  }

  toggleSeekbar() {
      this.seekbarMiniHidden = !this.seekbarMiniHidden;
  }
}
