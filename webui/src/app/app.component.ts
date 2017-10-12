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

import { Component, ViewChild } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { MatSidenav } from '@angular/material';
import { MatDialog } from '@angular/material';
import { ObservableMedia, MediaChange } from '@angular/flex-layout';
import { OnInit } from '@angular/core';
import { DjdClientService } from './services/djd-client.service';
import { MenuService } from './services/menu.service';
import { PlayerService } from './services/player.service';
import { PlayingQueuesComponent } from './components/playing-queues.component';
import { VideoOptionsDialog } from './components/player/options-dialog.component';
import { Media } from './models/media.model';
declare var DeejaydApp: any;


@Component({
  selector: 'my-app',
  template: `
    <mat-menu #mainMenu="matMenu">
      <button mat-menu-item
              *ngIf="menu.isClearActive()"
              (click)="menu.clear()" i18n>Clear</button>
      <button mat-menu-item
              *ngIf="menu.isShuffleActive()"
              (click)="menu.shuffle()" i18n>Shuffle</button>

      <button mat-menu-item
             *ngIf="menu.isUpdateLibraryActive()"
             (click)="menu.updateLibrary()" i18n>Update library</button>

      <button mat-menu-item
             *ngIf="menu.isWrAddCategoryActive()"
             (click)="menu.wrAddCategory()" i18n>Add a category</button>
      <button mat-menu-item
             *ngIf="menu.isWrAddActive()"
             (click)="menu.addWebradio()" i18n>Add a Webradio</button>
    </mat-menu>

    <mat-toolbar class="djd-toolbar" color="primary">
      <button fxHide [fxShow.lt-md]="true" mat-icon-button (click)=sidenav.toggle()>
        <mat-icon>menu</mat-icon>
      </button>
      <span>{{title}}</span>
      <div style="flex: 1 1 auto;"></div>
      <button mat-icon-button
              [disabled]="playingMedia == null || playingMedia.type != 'video'"
              (click)="openOptionsDialog()">
        <mat-icon>movie</mat-icon>
      </button>
      <button mat-icon-button [matMenuTriggerFor]="mainMenu">
        <mat-icon>more_vert</mat-icon>
      </button>
    </mat-toolbar>

    <mat-sidenav-container class="djd-main-container">
      <mat-sidenav #sidenav mode="{{sidenavMode}}" opened="{{sidenavOpened}}">
        <div fxLayout="column" class="djd-sidenav-container">
          <a mat-button
             [class.djd-menu-active]="router.url == '/playing'"
             routerLink="/playing">
            <mat-icon style="color:#404040;">queue</mat-icon>
            <ng-container i18n>Now Playing</ng-container>
          </a>
          <a mat-button
             [class.djd-menu-active]="router.url == '/music'"
             routerLink="/music">
            <mat-icon style="color:#404040;">library_music</mat-icon>
            <ng-container i18n>Music Library</ng-container>
          </a>
          <a mat-button
             [class.djd-menu-active]="router.url == '/video'"
             routerLink="/video">
            <mat-icon style="color:#404040;">video_library</mat-icon>
            <ng-container i18n>Video Library</ng-container>
          </a>
          <a mat-button
             [class.djd-menu-active]="router.url == '/radio'"
             routerLink="/radio">
            <mat-icon style="color:#404040;">radio</mat-icon>
            <ng-container i18n>Radio</ng-container>
          </a>
        </div>
      </mat-sidenav>

      <!-- primary content -->
      <router-outlet></router-outlet>
    </mat-sidenav-container>

    <div class="djd-player-container">
      <djd-player></djd-player>
    </div>
    `
})
export class AppComponent implements OnInit {
  @ViewChild("sidenav") sidenav: MatSidenav;
  public title: string = 'Deejayd';
  public sidenavOpened: boolean = false;
  public sidenavMode: String = "side";
  public playingMedia: Media;

  constructor(public router: Router, public media: ObservableMedia,
    public client: DjdClientService, public menu: MenuService,
    public player: PlayerService, public dialog: MatDialog) {
    media.asObservable().subscribe((change: MediaChange) => {
      this.setLayout();
    });
  }

  ngOnInit(): void {
    // connect to server
    this.client.connect(DeejaydApp.options.root_url + "rpc")
      .subscribe((message: any) => {
      });

    // adapt layout to device
    this.setLayout();

    // watch route changes to update title
    this.router.events.filter((evt) => evt instanceof NavigationEnd)
      .subscribe((evt: NavigationEnd) => {
        switch (evt.urlAfterRedirects) {
          case "/playing":
            this.title = "Now Playing";
            break;
          case "/music":
            this.title = "Music Library";
            break;
          case "/video":
            this.title = "Video Library";
            break;
          case "/radio":
            this.title = "Radio";
            break;
        }
        if (this.isMobile()) { // close the sidenav
          this.sidenav.close();
        }
      })

    // watch playingMedia to enabled/disabled video options
    this.player.playingMedia$.subscribe((m: Media) => {
      this.playingMedia = m;
    });
  }

  isMobile(): boolean {
    return this.media.isActive("lt-md");
  }

  setLayout(): void {
    this.sidenavMode = this.isMobile() ? "push" : "side";
    this.sidenavOpened = !this.isMobile();
  }

  openOptionsDialog(): void {
    this.player.getVideoOptions().subscribe((options: any) => {
      this.dialog.open(VideoOptionsDialog, {
        width: "80%",
        data: {
          options: options,
          media: this.playingMedia
        }
      });
    });
  }
}
