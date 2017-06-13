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

import { Component, Inject } from '@angular/core';
import { MD_DIALOG_DATA, MdDialogRef } from '@angular/material';
import { WebradioService } from '../../services/webradio.service'


@Component({
  selector: 'djd-wr-cat-dialog',
  template: `
    <h2 md-dialog-title i18n>
      Add new category
    </h2>

    <div md-dialog-content fxLayout="column">
        <md-input-container>
            <input mdInput #catName placeholder="Category name">
        </md-input-container>
    </div>

    <div md-dialog-actions>
      <button md-raised-button (click)="dialogRef.close()">
        <md-icon>cancel</md-icon>
        Cancel
      </button>
      <button md-raised-button
              (click)="addCategory(catName.value)">
        <md-icon>done</md-icon>
        Add
      </button>
    </div>
  `
})
export class WrCategoryDialogComponent {

  constructor( @Inject(MD_DIALOG_DATA) public data: any,
    public webradio: WebradioService,
    public dialogRef: MdDialogRef<WrCategoryDialogComponent>) { }

  addCategory(catName: string) {
    this.webradio.addCategory(this.data.source, catName);
    this.dialogRef.close();
  }
}
