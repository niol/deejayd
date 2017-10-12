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

@Component({
  selector: 'djd-playing-queues',
  template: `
  <mat-tab-group (change)="onTabChange($event)">
    <mat-tab label="Music">
      <djd-playlist name="audiopls" [hasRepeat]="true"></djd-playlist>
    </mat-tab>
    <mat-tab label="Queue">
      <djd-playlist name="audioqueue" [hasRepeat]="false"></djd-playlist>
    </mat-tab>
    <mat-tab label="Video">
      <djd-playlist name="videopls" [hasRepeat]="true"></djd-playlist>
    </mat-tab>
  </mat-tab-group>
  `
})
export class PlayingQueuesComponent implements OnInit {
  public selectedSource:string = "audiopls";

  constructor(private menu:MenuService) {}
  ngOnInit() {
    this.menu.register("nowplaying."+this.selectedSource);
  }

  onTabChange(event: MatTabChangeEvent):void {
    switch(event.index) {
      case 1:
        this.selectedSource = "audiopls";
        break;
      case 2:
        this.selectedSource = "audioqueue";
        break;
      case 2:
        this.selectedSource = "videopls";
        break;
    }
    this.menu.register("nowplaying."+this.selectedSource);
  }
}
