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

import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { Media } from '../models/media.model';
import { MatSelectChange, MatButtonToggleChange } from '@angular/material';
import { Subscription } from 'rxjs/Rx';
import { DjdClientService } from '../services/djd-client.service';
import { PlayerService } from '../services/player.service';
import { UtilsService } from '../services/utils.service';


interface MediaListStatus {
  id: number,
  length: number,
  timelength: number,
  playorder: string,
  repeat?: boolean
}

@Component({
  selector: 'djd-playlist',
  template: `
  <mat-menu #mediaMenu="matMenu">
    <button mat-menu-item (click)="play()" i18n>Play</button>
    <button mat-menu-item
                *ngIf="utils.hasLastPos(selectedMedia)"
                (click)="resume()"
                i18n>
      Resume at {{ utils.formatTime(selectedMedia.last_position) }}
    </button>
    <button mat-menu-item (click)="remove()" i18n>Remove</button>
  </mat-menu>

  <div fxLayout="row" fxLayoutAlign="start center" class="djd-medialist-header">
    <h3 fxFlex="1 1 100%">
      <span *ngIf="name.startsWith('audio')" i18n>
        {medias.length, plural, =0 {no song} =1 {one song} other {{{medias.length}} songs}}
      </span>
      <span *ngIf="name.startsWith('video')" i18n>
        {medias.length, plural, =0 {no video} =1 {one video} other {{{medias.length}} videos}}
      </span>
      <span>({{ timeDesc }})</span>
    </h3>
    <mat-button-toggle
              #repeatToggleButton
              *ngIf="hasRepeat"
              (change)="setRepeatOption(repeatToggleButton.checked)"
              [checked]="repeat">
      <mat-icon>repeat</mat-icon>
    </mat-button-toggle>
    <span style="width: 10px;"></span>
    <mat-form-field>
      <mat-select [ngModel]="playOrder"
                (change)="setOrderOption($event)">
        <mat-option value="inorder">In order</mat-option>
        <mat-option value="random">Random</mat-option>
        <mat-option value="onemedia">One Media</mat-option>
      </mat-select>
    </mat-form-field>
  </div>

  <ul class="djd-medialist">
      <li *ngFor="let media of medias">
        <div fxLayout="row" fxLayoutAlign="start center">
          <div fxFlex="1 1 100%" class="djd-medialist-item">
              <h4>{{getTitle(media)}}</h4>
              <p><em>{{utils.getMediaDesc(media)}}</em></p>
          </div>
          <div fxFlex="0 0 auto">
            <button mat-icon-button
                    (click)="select(media)"
                    [matMenuTriggerFor]="mediaMenu">
                <mat-icon>menu</mat-icon>
            </button>
          </div>
        </div>
      </li>
  </ul>
  `
})
export class PlaylistComponent implements OnInit, OnDestroy {
  @Input() name:string;
  @Input() hasRepeat:boolean;
  medias: Media[] = [];
  selectedMedia:Media = null;
  lastMediaPos:number = 0;
  timeDesc:string = "";
  playOrder:string = "inorder";
  repeat:boolean = false;
  connectedSubscription:Subscription = null;

  constructor(private client:DjdClientService, private player:PlayerService,
              public utils:UtilsService) { }

  ngOnInit() {
    this.connectedSubscription = this.client.isConnected$.subscribe((connected:boolean) => {
      if (connected) {
        this.update();
        this.setSubscriptions();
      }
    });
  }

  ngOnDestroy() {
    if (this.connectedSubscription != null) {
      this.connectedSubscription.unsubscribe();
    }
  }

  setSubscriptions():void {
    this.client.subscribe(`${this.name}.update`, (signal:Object) => {
        this.update();
    });
  }

  update():void {
    this.client.sendCommand(`${this.name}.getStatus`, [])
               .subscribe((infos: MediaListStatus) => {
      this.timeDesc = `${this.utils.formatTime(infos.timelength)}`;
      this.playOrder = infos.playorder;
      if (this.hasRepeat) {
        this.repeat = infos.repeat;
      }
    });
    this.client.sendCommand(`${this.name}.get`, [])
               .subscribe((m_list: Media[]) => {
                   this.medias = m_list;
               });
  }

  getTitle(m: Media): string {
    return `${m.title} (${this.utils.formatTime(m.length)})`;
  }

  select(m: Media) {
    this.selectedMedia = m;
  }

  play():void {
    this.player.goTo(this.selectedMedia.id, "id", this.name);
  }

  resume():void {
    this.player.goTo(this.selectedMedia.id, "id", this.name,
                     this.selectedMedia.last_position);
  }

  remove():void {
    this.client.sendSimpleCmd(`${this.name}.remove`, [[this.selectedMedia.id]]);
  }

  setRepeatOption(value:boolean) {
    this.client.sendSimpleCmd(`${this.name}.setOption`, ["repeat", value]);
  }

  setOrderOption(evt:MatSelectChange) {
    this.client.sendSimpleCmd(`${this.name}.setOption`, ["playorder", evt.value]);
  }
}
