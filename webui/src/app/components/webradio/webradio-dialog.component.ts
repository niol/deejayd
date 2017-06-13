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

import { Component, Inject, OnInit } from '@angular/core';
import { MD_DIALOG_DATA, MdDialogRef } from '@angular/material';
import { WebradioService, WebradioCategory } from '../../services/webradio.service'


@Component({
  selector: 'djd-wr-dialog',
  template: `
    <h2 md-dialog-title i18n>
      Add new webradio
    </h2>

    <div md-dialog-content fxLayout="column">
        <md-select [(ngModel)]="selectedCategory">
          <md-option *ngFor="let cat of categories" [value]="cat.id">
            {{cat.name}}
          </md-option>
        </md-select>
        <md-input-container>
            <input mdInput #wrName placeholder="Webradio name">
        </md-input-container>
        <md-input-container>
            <input mdInput #wrUrl placeholder="Webradio url">
        </md-input-container>
    </div>

    <div md-dialog-actions>
      <button md-raised-button (click)="dialogRef.close()">
        <md-icon>cancel</md-icon>
        Cancel
      </button>
      <button md-raised-button
              [disabled]="wrName.value == '' || wrUrl.value == '' || categories.length == 0"
              (click)="addWebradio(wrName.value, wrUrl.value)">
        <md-icon>done</md-icon>
        Add
      </button>
    </div>
  `
})
export class WebradioDialogComponent implements OnInit {
  public selectedCategory:number = -1;
  public categories:WebradioCategory[] = [];

  constructor( @Inject(MD_DIALOG_DATA) public data: any,
               public webradio: WebradioService,
               public dialogRef: MdDialogRef<WebradioDialogComponent>) { }

  ngOnInit() {
    this.webradio.getCategories(this.data.source).subscribe((catList: WebradioCategory[]) => {
        this.categories = catList;
        if (catList.length > 0) {
          this.selectedCategory = catList[0].id;
        }
    });
  }

  addWebradio(wrName: string, wrUrl:string) {
    this.webradio.addWebradio(this.data.source, this.selectedCategory, wrName, wrUrl);
    this.dialogRef.close();
  }
}
