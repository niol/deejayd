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

import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef, MatSelectChange } from '@angular/material';
import { PlayerService } from '../../services/player.service';
import { Media } from '../../models/media.model';

@Component({
  selector: 'djd-seek-dialog',
  template: `
    <h2 mat-dialog-title i18n>
      Seek Dialog
    </h2>

    <div mat-dialog-content fxLayout="column">
      <div fxLayout="row"
           fxLayoutAlign="center center"
           class="djd-dialog-option"
           [hidden]="data <= 3600">
        <div fxFlex="1 1 100%" class="djd-dialog-label">Hours</div>
        <div fxFlex="2 2 100%">
            <mat-input-container>
              <input matInput #hoursInput placeholder="Hours"
                     type=number
                     min=0
                     max=60
                     step=1
                     value=0>
            </mat-input-container>
        </div>
      </div>

      <div fxLayout="row"
           fxLayoutAlign="center center"
           class="djd-dialog-option"
           [hidden]="data <= 60">
        <div fxFlex="1 1 100%" class="djd-dialog-label">Minutes</div>
        <div fxFlex="2 2 100%">
            <mat-input-container>
              <input matInput #minutesInput placeholder="Minutes"
                     type=number
                     min=0
                     max=60
                     step=1
                     value=0>
            </mat-input-container>
        </div>
      </div>

      <div fxLayout="row"
           fxLayoutAlign="center center"
           class="djd-dialog-option">
        <div fxFlex="1 1 100%" class="djd-dialog-label">Seconds</div>
        <div fxFlex="2 2 100%">
            <mat-input-container>
              <input matInput #secondsInput placeholder="Seconds"
                     type=number
                     min=0
                     max=60
                     step=1
                     value=0>
            </mat-input-container>
        </div>
      </div>
    </div>

    <div mat-dialog-actions>
      <button mat-raised-button (click)="dialogRef.close()">
        <mat-icon>close</mat-icon>
        Close
      </button>
      <button mat-raised-button
              (click)="seek(hoursInput.value, minutesInput.value, secondsInput.value)">
        <mat-icon>send</mat-icon>
        Seek
      </button>
    </div>
  `
})
export class SeekDialogComponent {

  constructor(@Inject(MAT_DIALOG_DATA) public data: any,
              public dialogRef: MatDialogRef<SeekDialogComponent>,
              private player:PlayerService) { }

  seek(hours:string, minutes:string, seconds:string) {
    let value:number = parseInt(hours)*3600 + parseInt(minutes)*60 + parseInt(seconds);
    this.player.seek(value, false);
  }
}
