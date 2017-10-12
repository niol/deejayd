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
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';
import { WebradioService, WebradioCategory } from '../../services/webradio.service'


@Component({
  selector: 'djd-wr-dialog',
  template: `
    <h2 mat-dialog-title i18n>
      Add new webradio
    </h2>

    <div mat-dialog-content fxLayout="column">
        <mat-select [(ngModel)]="selectedCategory">
          <mat-option *ngFor="let cat of categories" [value]="cat.id">
            {{cat.name}}
          </mat-option>
        </mat-select>
        <mat-input-container>
            <input matInput #wrName placeholder="Webradio name">
        </mat-input-container>
        <mat-input-container>
            <input matInput #wrUrl placeholder="Webradio url">
        </mat-input-container>
    </div>

    <div mat-dialog-actions>
      <button mat-raised-button (click)="dialogRef.close()">
        <mat-icon>cancel</mat-icon>
        Cancel
      </button>
      <button mat-raised-button
              [disabled]="wrName.value == '' || wrUrl.value == '' || categories.length == 0"
              (click)="addWebradio(wrName.value, wrUrl.value)">
        <mat-icon>done</mat-icon>
        Add
      </button>
    </div>
  `
})
export class WebradioDialogComponent implements OnInit {
  public selectedCategory:number = -1;
  public categories:WebradioCategory[] = [];

  constructor( @Inject(MAT_DIALOG_DATA) public data: any,
               public webradio: WebradioService,
               public dialogRef: MatDialogRef<WebradioDialogComponent>) { }

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
