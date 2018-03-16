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

import { Component, Input } from '@angular/core';
import { OnInit } from '@angular/core';
import { DjdClientService } from '../../services/djd-client.service';
import { PlayerService } from '../../services/player.service';
import { Folder, Media } from '../../models/media.model';
import { UtilsService } from '../../services/utils.service';

interface PathObject {
  path: string,
  name: string
}

@Component({
  selector: 'djd-folder-view',
  template: `
  <ol *ngIf="currentPath.length > 0" class="djd-breadcrumb" >
    <li *ngFor="let pObj of currentPath">
      <a (click)="getPath(pObj.path)">
        {{ pObj.name }}
      </a>
    </li>
    <li class="djd-active">{{ currentFolder }}</li>
  </ol>

  <div [ngSwitch]="loading" fxLayout="column">
    <mat-nav-list *ngSwitchCase="false" [disableRipple]="true">
      <mat-menu #libraryMenu="matMenu">
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

      <!-- folder -->
      <mat-list-item *ngFor="let folder of folders" (click)="getPath(folder.path)">
        <mat-icon mat-list-icon>folder</mat-icon>
        <div class="djd-library-item">
          <div>
            <span>{{ folder.name }}</span>
          </div>
          <div style="flex: 1 1 auto;"></div>
          <div>
            <button mat-icon-button
                    (click)="selectFolder(folder); $event.stopPropagation()"
                    [matMenuTriggerFor]="libraryMenu">
                <mat-icon>menu</mat-icon>
            </button>
          </div>
        </div>
      </mat-list-item>

      <!-- media -->
      <mat-list-item *ngFor="let media of medias">
        <mat-icon mat-list-icon>music_video</mat-icon>
        <div class="djd-library-item">
          <div>
            <span *ngIf="type == 'video' && media.play_count == 0">*</span>
            <span>{{ media.filename }}</span>
          </div>
          <div style="flex: 1 1 auto;"></div>
          <div>
            <button mat-icon-button
                    (click)="selectMedia(media)"
                    [matMenuTriggerFor]="libraryMenu">
                <mat-icon>menu</mat-icon>
            </button>
          </div>
        </div>
      </mat-list-item>
    </mat-nav-list>

    <div *ngSwitchCase="true" 
         fxFlex="1 1 auto"
         fxLayout="column"
         fxLayoutAlign="center center"
         fxLayoutGap="10px"
         class="djd-loading-container">
        <div style="height: 50px; width: 50px;"></div> 
        <mat-spinner></mat-spinner>
        <div i18n>Loading...</div>
    </div>
  </div>
    `
})
export class FolderViewComponent implements OnInit {
  @Input() type:string;
  currentPath:PathObject[] = [];
  currentFolder:string = "";
  loading:boolean = true;
  folders:Folder[] = [];
  medias:Media[] = [];
  selectedMedia:Media = null;
  selectedFolder:Folder = null;

  constructor(private client:DjdClientService, private player:PlayerService,
              private utils:UtilsService) { }

  ngOnInit(): void {
    this.client.isConnected$.subscribe((connected:boolean) => {
      if (connected) {
        this.getPath('');
      }
    });
  }

  getPath(path:string) {
    this.loading = true;
    this.client.sendCommand(`${this.type}lib.getDirContent`, [path])
               .subscribe((answer:any) => {
      this.folders = answer.directories as Folder[];
      this.medias = answer.files as Media[];

      this.currentPath = []
      if (path != "") {
        let parts:string[] = path.split("/");
        let rel_path:string = "";

        this.currentPath = [{path: "", name:"Home"}];
        parts.forEach((p:string, idx:number) => {
          if (idx < (parts.length-1)) {
            rel_path = rel_path == "" ? p : rel_path+"/"+p;
            this.currentPath.push({name: p, path:rel_path})
          } else {
            this.currentFolder = p
          }
        });
      }
      this.loading = false;
    });
  }

  isNew(media:Media) {
    return this.type == "video" && media.play_count == 0;
  }

  selectMedia(m: Media) {
    this.selectedMedia = m;
    this.selectedFolder = null;
  }

  selectFolder(f: Folder) {
    this.selectedFolder = f;
    this.selectedMedia = null;
  }

  play() {
    if (this.selectedFolder != null) {
      this.player.playFolder(this.selectedFolder.id, `${this.type}pls`);
    } else if (this.selectedMedia != null) {
      this.player.playMedia(this.selectedMedia.m_id, `${this.type}pls`);
    }
  }

  resume() {
    this.player.resumeMedia(this.selectedMedia.m_id, `${this.type}pls`,
                            this.selectedMedia.last_position - 30);
  }

  loadToPlaylist() {
    if (this.selectedFolder != null) {
      this.client.sendSimpleCmd(`${this.type}pls.loadFolders`,
                                [[this.selectedFolder.id], true]);
    } else if (this.selectedMedia != null) {
      this.client.sendSimpleCmd(`${this.type}pls.loadMedias`,
                                [[this.selectedMedia.m_id], true]);
    }
  }

  loadToQueue() {
    if (this.selectedFolder != null) {
      this.client.sendSimpleCmd(`${this.type}queue.loadFolders`,
                                [[this.selectedFolder.id], true]);
    } else if (this.selectedMedia != null) {
      this.client.sendSimpleCmd(`${this.type}queue.loadMedias`,
                                [[this.selectedMedia.m_id], true]);
    }
  }
}
