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
  selector: 'djd-player',
  template: `
  <div fxLayout='column' id="djd-player-toolbar">
    <div fxFlex="30px" fxLayout='row'>
        <div fxFlexFill fxLayoutAlign="center center">
            <span class="djd-current-media">{{currentMedia}}</span>
        </div>
    </div>
    <div fxFlex="55px" fxLayout='row'>
        <div fxFlex="1 1 250px"
             fxFlex.sm="1 1 300px"
             fxFlex.lt-sm="1 1 100%"
             fxLayoutAlign="center center">
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

            <button mat-button fxHide [fxShow.lt-md]="true"
                    (click)="openSeekDialog()"
                    [disabled]="seekbarState.length == 0">
                {{seekbarState.formatedPosition}} /
                {{seekbarState.formatedLength}}
            </button>

            <div fxHide [fxShow.lt-sm]="true">
                <button mat-icon-button
                        #vMiniButton
                        (click)="toggleVolumeMenu()">
                    <mat-icon>volume_up</mat-icon>
                </button>

                <div #volMenu class="djd-mini-vslider-box">
                    <mat-slider vertical
                        class="djd-mini-vslider"
                        *ngIf="!vSliderHidden"
                        (change)="player.setVolume($event.value)"
                        [ngModel]="volume"
                        [min]=0
                        [max]=100
                        [step]=5></mat-slider>
                </div>
            </div>
        </div>
        <div fxFlex="2 1 100%"
             fxLayoutAlign="center center"
             fxLayout="row"
             fxShow [fxHide.lt-md]="true">
            <button fxFlex="0 0 auto"
                    [disabled]="seekbarState.length == 0"
                    (click)="openSeekDialog()"
                    mat-button>
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
            <button fxFlex="0 0 auto"
                    [disabled]="seekbarState.length == 0"
                    (click)="openSeekDialog()"
                    mat-button>
                {{seekbarState.formatedLength}}
            </button>
        </div>
        <djd-volume fxFlex="1 1 250px"
                    fxFlex.sm="1 1 100%"
                    fxShow [fxHide.lt-sm]="true"></djd-volume>
    </div>
  </div>
    `
})
export class PlayerComponent implements OnInit {
  public isPlaying:boolean = false;
  public currentMedia:string = "no playing media";
  public seekbarState:SeekbarState;
  private seekTimer:Timer;
  public volume:number = 0;
  public vSliderHidden:boolean = true;

  constructor(public player:PlayerService, public dialog:MatDialog,
              private utils:UtilsService) {
    this.resetSeekbar();
    this.seekTimer = new Timer((val: number) => {
        this.player.seek(val, false);
    });
  }

  log(event:any) {
      console.log(event.value);
  }

  ngOnInit(): void {
    this.player.playerStatus$.subscribe((status:PlayerStatus) => {
      this.isPlaying = status.state == "play";
      this.volume = status.volume;
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
    this.player.playingMedia$.subscribe((media: Media) => {
        if (media == null) {
            this.currentMedia = "no playing media";
        } else {
            this.currentMedia = media.title;
            if (media.type == "song") {
                this.currentMedia += " - "+media["artist"];
            }
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

  toggleVolumeMenu() {
      this.vSliderHidden = !this.vSliderHidden;
  }
}
