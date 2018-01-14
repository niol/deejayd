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

import { Component, EventEmitter, Output, OnInit } from '@angular/core';
import { MatTabChangeEvent } from '@angular/material';
import { MenuService } from '../services/menu.service';
import { PlayerService, PlayerStatus } from '../services/player.service';

@Component({
  selector: 'djd-playing-queues',
  template: `
  <mat-tab-group (selectedTabChange)="onTabChange($event)">
    <mat-tab>
      <ng-template mat-tab-label>
        <mat-icon *ngIf="playingState == 'play:audiopls'">play_arrow</mat-icon>
        <mat-icon *ngIf="playingState == 'pause:audiopls'">pause</mat-icon>
        <ng-container i18n>Music</ng-container>
      </ng-template>
      <djd-playlist name="audiopls" 
                    [playingMediaId]="playingMedia.audiopls"
                    [hasRepeat]="true"></djd-playlist>
    </mat-tab>
    <mat-tab>
      <ng-template mat-tab-label>
        <mat-icon *ngIf="playingState == 'play:audioqueue'">play_arrow</mat-icon>
        <mat-icon *ngIf="playingState == 'pause:audioqueue'">pause</mat-icon>
        <ng-container i18n>Queue</ng-container>
      </ng-template>
      <djd-playlist name="audioqueue" 
                    [playingMediaId]="playingMedia.audioqueue"
                    [hasRepeat]="false"></djd-playlist>
    </mat-tab>
    <mat-tab>
      <ng-template mat-tab-label>
        <mat-icon *ngIf="playingState == 'play:videopls'">play_arrow</mat-icon>
        <mat-icon *ngIf="playingState == 'pause:videopls'">pause</mat-icon>
        <ng-container i18n>Video</ng-container>
      </ng-template>
      <djd-playlist name="videopls"
                    [hasRepeat]="true" 
                    [playingMediaId]="playingMedia.videopls"></djd-playlist>
    </mat-tab>
  </mat-tab-group>
  `
})
export class PlayingQueuesComponent implements OnInit {
  public selectedSource:string = "audiopls";
  public playingState:string = "stop";
  public playingMedia:any = {
    audiopls: -1,
    audioqueue: -1,
    videopls: -1
  };

  constructor(public player:PlayerService, private menu:MenuService) {}

  ngOnInit() {
    this.player.playerStatus$.subscribe((status:PlayerStatus) => {
      this.playingState = status.state;
      this.playingMedia = {
        audiopls: -1,
        audioqueue: -1,
        videopls: -1
      };

      if (status.state != "stop") { // update seekbar
        let current:string[] = status.current.split(":");
        this.playingState += ":"+current[2];
        this.playingMedia[current[2]] = parseInt(current[1]);
      }
    });
  }

  onTabChange(event: MatTabChangeEvent):void {
    switch(event.index) {
      case 0:
        this.selectedSource = "audiopls";
        break;
      case 1:
        this.selectedSource = "audioqueue";
        break;
      case 2:
        this.selectedSource = "videopls";
        break;
    }
    this.menu.register("nowplaying."+this.selectedSource);
  }
}
