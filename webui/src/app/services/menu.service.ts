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

import { Injectable, Component } from '@angular/core';
import { Observable, BehaviorSubject } from "rxjs/Rx";
import { DjdClientService } from './djd-client.service';
import { MatDialog } from '@angular/material';
import { WrCategoryDialogComponent } from '../components/webradio/category-dialog.component';
import { WebradioDialogComponent } from '../components/webradio/webradio-dialog.component';

export interface LibraryUpdateState {
  name: string,
  updating: boolean
}

@Injectable()
export class MenuService {
  public activeChild: string = "nowplaying.audiopls";
  private libUpdateState: BehaviorSubject<LibraryUpdateState> = new BehaviorSubject<LibraryUpdateState>({
    name: "audiolib",
    updating: false
  });
  public libUpdateState$: Observable<LibraryUpdateState> = this.libUpdateState.asObservable();

  constructor(private client: DjdClientService, public dialog: MatDialog) { }

  register(component: string) {
    this.activeChild = component;
  }

  //
  // Playlist global actions
  //
  isClearActive(): boolean {
    return this.activeChild.startsWith("nowplaying");
  }

  clear(): void {
    let pls: string = this.activeChild.split(".")[1];
    this.client.sendSimpleCmd(`${pls}.clear`, []);
  }

  isShuffleActive(): boolean {
    if (this.activeChild.startsWith("nowplaying")) {
      let pls: string = this.activeChild.split(".")[1];
      return pls.endsWith("pls");
    }
    return false;
  }

  shuffle(): void {
    let pls: string = this.activeChild.split(".")[1];
    this.client.sendSimpleCmd(`${pls}.shuffle`, []);
  }

  //
  // library global actions
  //
  isUpdateLibraryActive(): boolean {
    return this.activeChild.endsWith("lib");
  }

  updateLibrary(): void {
    this.client.sendSimpleCmd(`${this.activeChild}.update`, []);
  }

  //
  // webradio global actions
  //
  isWrAddCategoryActive(): boolean {
    return this.activeChild == 'webradio.local';
  }

  wrAddCategory():void {
    let source:string = this.activeChild.split(".")[1];
    this.dialog.open(WrCategoryDialogComponent, { data: { source: source } });
  }

  isWrAddActive(): boolean {
    return this.activeChild == 'webradio.local';
  }

  addWebradio():void {
    let source:string = this.activeChild.split(".")[1];
    this.dialog.open(WebradioDialogComponent, { data: { source: source } });
  }
}
