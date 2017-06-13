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

import { Injectable } from '@angular/core';
import { Subject, Observable, BehaviorSubject } from "rxjs/Rx";
import { DjdClientService } from './djd-client.service';

export interface WebradioSource {
  name: string,
  label: string,
  editable: boolean
}

export interface WebradioCategory {
  name: string,
  id: number
}

export interface Webradio {
  title: string,
  wb_id: number,
}

@Injectable()
export class WebradioService {
  private sources: BehaviorSubject<WebradioSource[]> = new BehaviorSubject<WebradioSource[]>([]);
  public sources$ = this.sources.asObservable();
  private sourceUpdated: Subject<string> = new Subject();
  public sourceUpdated$ = this.sourceUpdated.asObservable();
  private labels = {
    local: "Local",
    icecast: "Icecast"
  };

  constructor(private client: DjdClientService) {
    client.isConnected$.subscribe((connected: boolean) => {
      if (connected) {
        this.getAvailableSources();
        this.setSubscriptions();
      }
    });
  }

  setSubscriptions(): void {
    this.client.subscribe("webradio.listupdate", (signal: any) => {
      this.sourceUpdated.next(signal.attrs.source);
    });
  }

  getAvailableSources() {
    this.client.sendCommand("webradio.getAvailableSources", []).subscribe((sources: any) => {
      let tempSources: WebradioSource[] = [];
      sources.forEach((element: any) => {
        tempSources.push({
          name: element.name,
          label: this.labels[element.name],
          editable: element.editable
        });
      });
      this.sources.next(tempSources);
    });
  }

  getCategories(sourceName: string) {
    return this.client.sendCommand("webradio.getSourceCategories", [sourceName]);
  }

  addCategory(sourceName: string, catName: string) {
    this.client.sendSimpleCmd("webradio.sourceAddCategory", [sourceName, catName]);
  }

  eraseCategory(sourceName: string, catId: number) {
    this.client.sendSimpleCmd("webradio.sourceDeleteCategories", [sourceName, [catId]])
  }

  getWebradios(sourceName: string, catId: number = null) {
    let args: string[] = [sourceName];
    if (catId != null) {
      args.push(catId.toString());
    }
    return this.client.sendCommand("webradio.getSourceContent", args);
  }

  addWebradio(sourceName: string, catId: number, wName: string, wUrl: string) {
    this.client.sendSimpleCmd("webradio.sourceAddWebradio", [sourceName, wName, [wUrl], catId]);
  }

  eraseWebradio(sourceName: string, wId: number) {
    this.client.sendSimpleCmd("webradio.sourceDeleteWebradios", [sourceName, [wId]]);
  }

  clearWebradios(sourceName: string) {
    this.client.sendSimpleCmd("webradio.sourceClearWebradios", [sourceName])
  }

  playWebradio(wbId: number) {
    this.client.sendSimpleCmd("webradio.playWebradio", [wbId])
  }
}
