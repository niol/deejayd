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
import { MenuService } from '../../services/menu.service';

@Component({
  selector: 'djd-video-library',
  template: `
  <mat-tab-group>
    <mat-tab i18n-label label="Filesystem">
      <djd-folder-view type="video"></djd-folder-view>
    </mat-tab>
    <mat-tab i18n-label label="Search">
      <djd-search-view type="video"
                       [tags]="searchTags">
      </djd-search-view>
    </mat-tab>
  </mat-tab-group>
  `
})
export class VideoLibraryComponent {
  public searchTags:string[] = ["title"]

  constructor(public menu:MenuService) {}
}
