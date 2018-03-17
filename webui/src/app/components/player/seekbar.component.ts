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
import {MatDialog} from '@angular/material';
import { Timer } from '../../models/timer.model';
import { Media } from '../../models/media.model';
import { PlayerService, PlayerStatus } from '../../services/player.service';
import { UtilsService } from '../../services/utils.service';
import { SeekDialogComponent } from './seek-dialog.component';

interface SeekbarState {
    length:number,
    formatedLength:string,
    position:number,
    formatedPosition: string,
    step:number
}

@Component({
  selector: 'djd-seekbar',
  template: `
    <div fxFlex="1 1 100%"
         style="width: 100%"
         fxLayoutAlign="center center"
         fxLayout="row">
        <button mat-button
                (click)="openSeekDialog()"
                [disabled]="seekbarState.length == 0">
            {{seekbarState.formatedPosition}}
        </button>
        <mat-slider
            fxFlex="1 1 100%"
            (change)="seek($event)"
            (input)="onSeekbarSlide($event.value)"
            [ngModel]="seekbarState.position"
            [disabled]="seekbarState.length == 0"
            [min]=0
            [max]=seekbarState.length
            [step]=seekbarState.step></mat-slider>
        <button mat-button
                (click)="openSeekDialog()"
                [disabled]="seekbarState.length == 0">
            {{seekbarState.formatedLength}}
        </button>
    </div>
    `
})
export class SeekbarComponent implements OnInit {
  public seekbarState:SeekbarState;
  private seekTimer:Timer;

  constructor(public player:PlayerService, public dialog:MatDialog,
              private utils:UtilsService) {
    this.resetSeekbar();
    this.seekTimer = new Timer((val: number) => {
        this.player.seek(val, false);
    });
  }

  ngOnInit(): void {
    this.player.playerStatus$.subscribe((status:PlayerStatus) => {
      if (status.state != "stop") { // update seekbar
        let time:string[] = status.time.split(":");
        this.seekbarState = {
            position: parseInt(time[0]),
            formatedPosition: this.utils.formatTime(parseInt(time[0])),
            length: parseInt(time[1]),
            formatedLength: this.utils.formatTime(parseInt(time[1])),
            step: 10
        };
      } else {
          this.resetSeekbar();
      }
    });
  }

  resetSeekbar():void {
    this.seekbarState = {
        length: 0,
        formatedLength: "00:00",
        position: 0,
        formatedPosition: "00:00",
        step: 1,
    }
  }

  seek(event: MatSliderChange):void {
    this.seekbarState.formatedPosition = this.utils.formatTime(event.value);
    this.seekTimer.update(event.value);
  }

  onSeekbarSlide(value:number):void {
      this.seekbarState.formatedPosition = this.utils.formatTime(value);
  }

  openSeekDialog() {
    this.dialog.open(SeekDialogComponent, {
        data: this.seekbarState.length
    })
  }
}