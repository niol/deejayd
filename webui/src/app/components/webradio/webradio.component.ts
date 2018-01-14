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

import { Component, OnInit } from '@angular/core';
import { MatTabChangeEvent } from '@angular/material';
import { WebradioService, WebradioSource } from '../../services/webradio.service'
import { MenuService } from '../../services/menu.service';


@Component({
  selector: 'djd-webradio',
  template: `
  <mat-tab-group (change)="onTabChange($event)">
    <mat-tab *ngFor="let source of sources" [label]="source.label">
        <djd-webradio-source [name]="source.name" [editable]="source.editable">
        </djd-webradio-source>
    </mat-tab>
  </mat-tab-group>
  `
})
export class WebradioComponent implements OnInit {
  public sources: WebradioSource[] = [];

  constructor(private webradio: WebradioService, private menu: MenuService) { }
  ngOnInit() {
    this.webradio.sources$.subscribe((sList: WebradioSource[]) => {
      this.sources = sList;
    });
  }

  onTabChange(event: MatTabChangeEvent): void {
    this.menu.register("webradio." + this.sources[event.index].name);
  }
}
