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

import { Component, OnInit, Input } from '@angular/core';
import { MatDialog } from '@angular/material';
import { WebradioService, WebradioSource, WebradioCategory, Webradio } from '../../services/webradio.service'
import { ConfirmDialogComponent } from '../common/confirm-dialog.component';

@Component({
    selector: 'djd-webradio-source',
    template: `
      <mat-nav-list *ngIf="state == 'category'">
        <mat-menu #wrCatMenu="matMenu">
            <button mat-menu-item (click)="eraseCategory()" i18n>Erase</button>
        </mat-menu>

        <mat-list-item *ngFor="let cat of categories"
                      (click)="viewWebradioList(cat)">
            <div class="djd-list-item">
                <div> {{ cat.name }} </div>
                <div style="flex: 1 1 auto;"></div>
                <div>
                    <button mat-icon-button
                            *ngIf="editable"
                            (click)="selectCategory(cat); $event.stopPropagation()"
                            [matMenuTriggerFor]="wrCatMenu">
                        <mat-icon>menu</mat-icon>
                    </button>
                </div>
            </div>
        </mat-list-item>
      </mat-nav-list>

      <div *ngIf="state == 'webradio'">
        <ol class="djd-breadcrumb" >
            <li>
                <a (click)="viewCategoryList()" i18n>View all categories</a>
            </li>
            <li class="djd-active">{{selectedCategory.name}}</li>
        </ol>
        <mat-nav-list>
            <mat-menu #wrMenu="matMenu">
                <button mat-menu-item (click)="playWebradio()" i18n>Play</button>
                <button mat-menu-item *ngIf="editable" (click)="eraseWebradio()" i18n>Erase</button>
            </mat-menu>

            <mat-list-item *ngFor="let wr of webradios">
                <div class="djd-list-item">
                    <div> {{ wr.title }} </div>
                    <div style="flex: 1 1 auto;"></div>
                    <div>
                        <button mat-icon-button
                                (click)="selectWebradio(wr); $event.stopPropagation()"
                                [matMenuTriggerFor]="wrMenu">
                            <mat-icon>menu</mat-icon>
                        </button>
                    </div>
                </div>
            </mat-list-item>
        </mat-nav-list>
      </div>

      <div fxLayout="row" *ngIf="state == 'loading'" class="djd-loading-container">
        <mat-spinner></mat-spinner>
      </div>
  `
})
export class WebradioSourceComponent implements OnInit {
    @Input() name: string;
    @Input() editable: boolean;
    public state: string = "category"
    public categories: WebradioCategory[] = [];
    public selectedCategory: WebradioCategory = null;
    public webradios: Webradio[] = [];
    public selectedWebradio: Webradio = null;

    constructor(private webradio: WebradioService,
        private dialog: MatDialog) { }

    ngOnInit() {
        this.updateView();
        this.webradio.sourceUpdated$.subscribe((sourceName: string) => {
            if (this.name == sourceName) {
                this.updateView();
            }
        });
    }

    updateView() {
        if (this.state == "category") {
            this.viewCategoryList();
        } else if (this.state == "webradio") {
            this.viewWebradioList(this.selectedCategory);
        }
    }

    selectCategory(cat: WebradioCategory) {
        this.selectedCategory = cat;
    }

    eraseCategory() {
        let dialogRef = this.dialog.open(ConfirmDialogComponent, {
            data: {
                action: 'Erase',
                message: 'Are you sure you want to erase this category ?'
            }
        });
        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                this.webradio.eraseCategory(this.name, this.selectedCategory.id);
            }
        });
    }

    viewCategoryList() {
        this.state = "loading";
        this.webradio.getCategories(this.name).subscribe((catList: WebradioCategory[]) => {
            this.categories = catList;
            this.state = "category"
        });
    }

    viewWebradioList(cat: WebradioCategory) {
        this.state = "loading";
        this.webradio.getWebradios(this.name, cat.id).subscribe((wrList: Webradio[]) => {
            this.webradios = wrList;
            this.selectedCategory = cat;
            this.state = "webradio";
        });
    }

    selectWebradio(wr: Webradio) {
        this.selectedWebradio = wr;
    }

    playWebradio() {
        this.webradio.playWebradio(this.selectedWebradio.w_id);
    }

    eraseWebradio() {
        let dialogRef = this.dialog.open(ConfirmDialogComponent, {
            data: {
                action: 'Erase',
                message: 'Are you sure you want to erase this webradio ?'
            }
        });
        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                this.webradio.eraseWebradio(this.name, this.selectedWebradio.w_id);
            }
        });
    }

}
