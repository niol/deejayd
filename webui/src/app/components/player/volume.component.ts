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
import { PlayerService, PlayerStatus } from '../../services/player.service'

@Component({
  selector: 'djd-volume',
  template: `
        <div fxFlex="1 1 100%" fxLayoutAlign="center center">
            <button fxFlex="0 0 auto" mat-icon-button (click)=player.setVolumeRelative(-5)>
                <mat-icon>volume_down</mat-icon>
            </button>
            <mat-slider
                fxFlex="1 1 100%"
                class="djd-volume-slider"
                (change)="updateVolume($event)"
                [ngModel]="volume"
                [min]=0
                [max]=100
                [tick-interval]=10
                [step]=5></mat-slider>
            <button fxFlex="0 0 auto" mat-icon-button (click)=player.setVolumeRelative(5)>
                <mat-icon>volume_up</mat-icon>
            </button>
        </div>
    `
})
export class VolumeComponent implements OnInit {
  private volumeTimer:Timer;
  public volume:number = 0;

  constructor(public player:PlayerService) {
    this.volumeTimer = new Timer((val: number) => {
      this.player.setVolume(val)
    });
  }

  ngOnInit(): void {
    this.player.playerStatus$.subscribe((status:PlayerStatus) => {
        this.volume = status.volume;
    });
  }

  updateVolume(event: MatSliderChange):void {
    this.volumeTimer.update(event.value);
  }
}
