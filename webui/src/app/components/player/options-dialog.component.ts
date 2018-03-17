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

import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef, MatSelectChange } from '@angular/material';
import { PlayerService } from '../../services/player.service';
import { Media } from '../../models/media.model';

@Component({
  selector: 'djd-options-dialog',
  template: `
    <h2 mat-dialog-title i18n>
      Video options
    </h2>

    <div mat-dialog-content fxLayout="column">
      <div fxLayout="row"
           fxLayoutAlign="center center"
           class="djd-dialog-option"
           *ngIf="data.options['aspect-ratio']">
        <div fxFlex="1 1 100%" class="djd-dialog-label" i18n>Aspect Ratio</div>
        <div fxFlex="2 2 100%">
            <mat-select [ngModel]="playingMedia.playing_state['aspect-ratio']"
                       (change)="setOption('aspect-ratio', $event.value)">
              <mat-option *ngFor="let aspect of aspectRatios" [value]="aspect">
                {{aspect}}
              </mat-option>
            </mat-select>
        </div>
      </div>

      <div fxLayout="row"
           fxLayoutAlign="center center"
           class="djd-dialog-option"
           *ngIf="data.options['current-audio']">
        <div fxFlex="1 1 100%" class="djd-dialog-label" i18n>Audio channels</div>
        <div fxFlex="2 2 100%">
            <mat-select [ngModel]="playingMedia.playing_state['current-audio']"
                       (change)="setOption('current-audio', $event.value)">
              <mat-option *ngFor="let channel of playingMedia.audio_channels"
                         [value]="channel.idx">
                {{channel.lang}}
              </mat-option>
            </mat-select>
        </div>
      </div>

      <div fxLayout="row"
           fxLayoutAlign="center center"
           class="djd-dialog-option"
           *ngIf="data.options['av-offset']">
        <div fxFlex="2 2 100%">
            <mat-input-container>
              <input matInput #avOffsetInput i18n-placeholder placeholder="A/V offset"
                     (keyUp)=0
                     type=number
                     step=100
                     [value]="playingMedia.playing_state['av-offset']">
            </mat-input-container>
        </div>
        <div>
            <button (click)="setOption('av-offset', avOffsetInput.value)"
                    mat-icon-button>
              <mat-icon>send</mat-icon>
            </button>
        </div>
      </div>

      <div fxLayout="row"
           fxLayoutAlign="center center"
           class="djd-dialog-option"
           *ngIf="data.options['current-sub'] && playingMedia.hasOwnProperty('sub_channels')">
        <div fxFlex="1 1 100%" class="djd-dialog-label" i18n>Subtitle channels</div>
        <div fxFlex="2 2 100%">
            <mat-select [ngModel]="playingMedia.playing_state['current-sub']"
                       (change)="setOption('current-sub', $event.value)">
              <mat-option *ngFor="let channel of playingMedia.sub_channels"
                         [value]="channel.idx">
                {{channel.lang}}
              </mat-option>
            </mat-select>
        </div>
      </div>

      <div fxLayout="row"
           fxLayoutAlign="center center"
           class="djd-dialog-option"
           *ngIf="data.options['sub-offset']">
        <div >
            <mat-input-container>
              <input matInput #subOffsetInput i18n-placeholder placeholder="Subtitle offset"
                     (keyUp)=0
                     type=number
                     step=100
                     [value]="playingMedia.playing_state['sub-offset']">
            </mat-input-container>
        </div>
        <div>
            <button (click)="setOption('sub-offset', subOffsetInput.value)"
                    mat-icon-button>
              <mat-icon>send</mat-icon>
            </button>
        </div>
      </div>
    </div>

    <div mat-dialog-actions>
      <button mat-raised-button (click)="dialogRef.close()">
        <mat-icon>close</mat-icon>
        <ng-container i18n>Close</ng-container>
      </button>
    </div>
  `
})
export class VideoOptionsDialog implements OnInit {
    public playingMedia:Media;
    public options:any;
    public aspectRatios:string[] = [
        "auto",
        "1:1",
        "4:3",
        "16:9",
        "16:10",
        "5:4"
    ]
  constructor(@Inject(MAT_DIALOG_DATA) public data: any,
              public dialogRef: MatDialogRef<VideoOptionsDialog>,
              private player:PlayerService) {
    this.playingMedia = data.media;
    this.options = {
      'current-text': true
    }
  }

  ngOnInit() {
    this.player.playingMedia$.subscribe((m: Media) => {
      this.playingMedia = m;
    });
  }

  setOption(option:string, value:number|string) {
    this.player.setVideoOption(option, value);
  }
}
