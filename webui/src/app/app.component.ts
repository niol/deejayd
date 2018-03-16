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

import { Component, ViewChild, LOCALE_ID, Inject } from '@angular/core';
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
  selector: 'djd-app',
  template: `
  <div class="djd-main-container" fxLayout="column">
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
      <button *ngIf="!loading" 
              fxHide [fxShow.lt-md]="true" 
              mat-icon-button (click)=sidenav.toggle()>
        <mat-icon>menu</mat-icon>
      </button>

      <span *ngIf="router.url == '/playing'" i18n>Now Playing</span>
      <span *ngIf="router.url == '/music'" i18n>Music Library</span>
      <span *ngIf="router.url == '/video'" i18n>Video Library</span>
      <span *ngIf="router.url == '/radio'" i18n>Radio</span>

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

    <div *ngIf="loading" 
         fxFlex="1 1 auto"
         fxLayout="column"
         fxLayoutAlign="center center"
         fxLayoutGap="10px"
         class="djd-main-loading">
        <mat-spinner [color]="accent"></mat-spinner>
        <div i18n>Wait for the connection to the server...</div>
    </div>

    <mat-sidenav-container 
         [fxHide]="loading"
         fxFlex="1 1 auto" 
         style="overflow-y: auto;">
      <mat-sidenav #sidenav mode="{{sidenavMode}}" opened="{{sidenavOpened}}">
        <div fxLayout="column" class="djd-sidenav-container">
          <a mat-button
             routerLinkActive="djd-menu-active"
             routerLink="/playing">
            <mat-icon style="color:#404040;">queue</mat-icon>
            <ng-container i18n>Now Playing</ng-container>
          </a>
          <a mat-button
             routerLinkActive="djd-menu-active"
             routerLink="/music">
            <mat-icon style="color:#404040;">library_music</mat-icon>
            <ng-container i18n>Music Library</ng-container>
          </a>
          <a mat-button
             routerLinkActive="djd-menu-active"
             routerLink="/video">
            <mat-icon style="color:#404040;">video_library</mat-icon>
            <ng-container i18n>Video Library</ng-container>
          </a>
          <a mat-button
             routerLinkActive="djd-menu-active"
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
  </div>
    `
})
export class AppComponent implements OnInit {
  @ViewChild("sidenav") sidenav: MatSidenav;
  public loading: boolean = true;
  public title: string = 'Deejayd';
  public sidenavOpened: boolean = false;
  public sidenavMode: String = "side";
  public playingMedia: Media;

  constructor(public router: Router, public media: ObservableMedia,
    public client: DjdClientService, public menu: MenuService,
    public player: PlayerService, public dialog: MatDialog,
    @Inject(LOCALE_ID) protected localeId: string) {
    media.asObservable().subscribe((change: MediaChange) => {
      this.setLayout();
    });
  }

  ngOnInit(): void {
    this.client.init(DeejaydApp.options.root_url + "rpc")
    this.client.isConnected$.subscribe((connected:boolean) => {
      this.loading = !connected;
    });

    // adapt layout to device
    this.setLayout();

    // watch route changes to update title and global menu
    this.router.events.filter((evt) => evt instanceof NavigationEnd)
      .subscribe((evt: NavigationEnd) => {
        switch (evt.urlAfterRedirects) {
          case "/playing":
            this.menu.register("nowplaying.audiopls");
            break;
          case "/music":
            this.menu.register("audiolib");
            break;
          case "/video":
            this.menu.register("videolib");
            break;
          case "/radio":
            this.menu.register("webradio.local");
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
    this.sidenavMode = this.isMobile() ? "over" : "side";
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
