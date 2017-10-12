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
           *ngIf="data.options.aspect-ratio">
        <div fxFlex="1 1 100%" class="djd-dialog-label">Aspect Ratio</div>
        <div fxFlex="2 2 100%">
            <mat-select [ngModel]="playingMedia.aspect_ratio"
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
           *ngIf="data.options.current-audio">
        <div fxFlex="1 1 100%" class="djd-dialog-label">Audio channels</div>
        <div fxFlex="2 2 100%">
            <mat-select [ngModel]="playingMedia.audio_idx"
                       (change)="setOption('current-audio', $event.value)">
              <mat-option *ngFor="let channel of playingMedia.audio"
                         [value]="channel.ix">
                {{channel.lang}}
              </mat-option>
            </mat-select>
        </div>
      </div>

      <div fxLayout="row"
           fxLayoutAlign="center center"
           class="djd-dialog-option"
           *ngIf="data.options.av-offset">
        <div fxFlex="1 1 100%" class="djd-dialog-label">Audio/Video offset</div>
        <div fxFlex="2 2 100%">
            <mat-input-container>
              <input matInput #avOffsetInput placeholder="A/V offset"
                     (keyUp)=0
                     type=number
                     step=100
                     [value]="playingMedia.av_offset">
            </mat-input-container>
        </div>
        <div fxFlex="2 2 100%">
            <button (click)="setOption('av-offset', avOffsetInput.value)"
                    mat-icon-button>
              <mat-icon>send</mat-icon>
            </button>
        </div>
      </div>

      <div fxLayout="row"
           fxLayoutAlign="center center"
           class="djd-dialog-option"
           *ngIf="data.options.current-sub && playingMedia.hasOwnProperty('subtitle')">
        <div fxFlex="1 1 100%" class="djd-dialog-label">Subtitle channels</div>
        <div fxFlex="2 2 100%">
            <mat-select [ngModel]="playingMedia.subtitle_idx"
                       (change)="setOption('current-text', $event.value)">
              <mat-option *ngFor="let channel of playingMedia.subtitle"
                         [value]="channel.ix">
                {{channel.lang}}
              </mat-option>
            </mat-select>
        </div>
      </div>

      <div fxLayout="row"
           fxLayoutAlign="center center"
           class="djd-dialog-option"
           *ngIf="data.options.sub-offset">
        <div fxFlex="1 1 100%" class="djd-dialog-label">Audio/Subtitle offset</div>
        <div fxFlex="2 2 100%">
            <mat-input-container>
              <input matInput #subOffsetInput placeholder="Subtitle offset"
                     (keyUp)=0
                     type=number
                     step=100
                     [value]="playingMedia.sub_offset">
            </mat-input-container>
        </div>
        <div fxFlex="2 2 100%">
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
        Close
      </button>
    </div>
  `
})
export class VideoOptionsDialog implements OnInit {
    public playingMedia:Media;
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
