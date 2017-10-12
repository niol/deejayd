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

import { Component, Input, OnInit } from '@angular/core';
import { DjdClientService } from '../../services/djd-client.service';
import { PlayerService } from '../../services/player.service';
import { Media } from '../../models/media.model';
import { MediaBasicFilter } from '../../models/filter.model';
import { UtilsService } from '../../services/utils.service';

@Component({
  selector: 'djd-search-view',
  template: `
  <div style="width:99%" fxLayout="column">
    <div fxLayout="row" fxLayoutAlign="center center">
        <mat-input-container fxFlex="1 1 100%">
            <input matInput #pattern placeholder="search">
        </mat-input-container>
        <div fxFlex="0 0 auto">
            <mat-select [(ngModel)]="selectedTag">
              <mat-option *ngFor="let tag of tags" [value]="tag">
                {{tag}}
              </mat-option>
            </mat-select>
        </div>
        <button fxFlex="0 0 auto" mat-raised-button
                (click)="search(pattern.value)">
            <mat-icon>search</mat-icon>
            Search
        </button>
    </div>

    <div fxFlex="1 1 100%" fxLayout="column">
        <h4 i18n>Search results</h4>
        <mat-menu #searchMenu="matMenu">
            <button mat-menu-item (click)="play()" i18n>Play</button>
            <button mat-menu-item
                        *ngIf="utils.hasLastPos(selectedMedia)"
                        (click)="resume()"
                        i18n>
              Resume at {{ utils.formatTime(selectedMedia.last_position) }}
            </button>
            <button mat-menu-item (click)="loadToPlaylist()" i18n>Add to playlist</button>
            <button mat-menu-item
                    *ngIf="type == 'audio'"
                    (click)="loadToQueue()" i18n>Add to queue</button>
        </mat-menu>
        <div [ngSwitch]="loading">
            <ul *ngSwitchCase="false" class="djd-medialist">
                <li *ngFor="let media of results" style="width: 100%">
                  <div fxLayout="row" fxLayoutAlign="start center">
                    <div fxFlex="1 1 100%" class="djd-medialist-item">
                        <h4>{{getTitle(media)}}</h4>
                        <p><em>{{utils.getMediaDesc(media)}}</em></p>
                    </div>
                    <div fxFlex="0 0 auto">
                      <button mat-icon-button
                              (click)="select(media)"
                              [matMenuTriggerFor]="searchMenu">
                          <mat-icon>menu</mat-icon>
                      </button>
                    </div>
                  </div>
                </li>
            </ul>

            <div *ngSwitchCase="true" class="djd-loading-container">
                <mat-spinner></mat-spinner>
            </div>
        </div>
    </div>
  </div>
    `
})
export class SearchViewComponent implements OnInit {
  @Input() type:string;
  @Input() tags:string[];
  public selectedTag:string;
  public loading:boolean = false;
  public results:Media[] = [];
  public selectedMedia:Media;

  constructor(private client:DjdClientService, private player:PlayerService,
              public utils:UtilsService) { }

  ngOnInit() {
    if (this.tags.length > 0) {
      this.selectedTag = this.tags[0];
    }
  }

  select(m: Media) {
    this.selectedMedia = m;
  }

  play() {
    this.player.playMedia(this.selectedMedia.m_id, `${this.type}pls`);
  }

  resume() {
    this.player.resumeMedia(this.selectedMedia.m_id, `${this.type}pls`,
                            this.selectedMedia.last_position - 30);
  }

  loadToPlaylist() {
    this.client.sendSimpleCmd(`${this.type}pls.loadMedias`,
                              [[this.selectedMedia.m_id], true]);
  }

  loadToQueue() {
    this.client.sendSimpleCmd(`${this.type}queue.loadMedias`,
                              [[this.selectedMedia.m_id], true]);
  }
  search(pattern:string) {
    this.loading = true;
    let filter:MediaBasicFilter = new MediaBasicFilter("contains", this.selectedTag, pattern);
    this.client.sendCommand(`${this.type}lib.search`, [filter.dump()])
               .subscribe((medias:Media[]) => {
      this.results = medias;
      this.loading = false;
    });
  }

  getTitle(m: Media): string {
    return `${m.title} (${this.utils.formatTime(m.length)})`;
  }
}
