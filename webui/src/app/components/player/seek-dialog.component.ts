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
import { MD_DIALOG_DATA, MdDialogRef, MdSelectChange } from '@angular/material';
import { PlayerService } from '../../services/player.service';
import { Media } from '../../models/media.model';

@Component({
  selector: 'djd-seek-dialog',
  template: `
    <h2 md-dialog-title i18n>
      Seek Dialog
    </h2>

    <div md-dialog-content fxLayout="column">
      <div fxLayout="row"
           fxLayoutAlign="center center"
           class="djd-dialog-option"
           [hidden]="data <= 3600">
        <div fxFlex="1 1 100%" class="djd-dialog-label">Hours</div>
        <div fxFlex="2 2 100%">
            <md-input-container>
              <input mdInput #hoursInput placeholder="Hours"
                     type=number
                     min=0
                     max=60
                     step=1
                     value=0>
            </md-input-container>
        </div>
      </div>

      <div fxLayout="row"
           fxLayoutAlign="center center"
           class="djd-dialog-option"
           [hidden]="data <= 60">
        <div fxFlex="1 1 100%" class="djd-dialog-label">Minutes</div>
        <div fxFlex="2 2 100%">
            <md-input-container>
              <input mdInput #minutesInput placeholder="Minutes"
                     type=number
                     min=0
                     max=60
                     step=1
                     value=0>
            </md-input-container>
        </div>
      </div>

      <div fxLayout="row"
           fxLayoutAlign="center center"
           class="djd-dialog-option">
        <div fxFlex="1 1 100%" class="djd-dialog-label">Seconds</div>
        <div fxFlex="2 2 100%">
            <md-input-container>
              <input mdInput #secondsInput placeholder="Seconds"
                     type=number
                     min=0
                     max=60
                     step=1
                     value=0>
            </md-input-container>
        </div>
      </div>
    </div>

    <div md-dialog-actions>
      <button md-raised-button (click)="dialogRef.close()">
        <md-icon>close</md-icon>
        Close
      </button>
      <button md-raised-button
              (click)="seek(hoursInput.value, minutesInput.value, secondsInput.value)">
        <md-icon>send</md-icon>
        Seek
      </button>
    </div>
  `
})
export class SeekDialogComponent {

  constructor(@Inject(MD_DIALOG_DATA) public data: any,
              public dialogRef: MdDialogRef<SeekDialogComponent>,
              private player:PlayerService) { }

  seek(hours:string, minutes:string, seconds:string) {
    let value:number = parseInt(hours)*3600 + parseInt(minutes)*60 + parseInt(seconds);
    this.player.seek(value, false);
  }
}
