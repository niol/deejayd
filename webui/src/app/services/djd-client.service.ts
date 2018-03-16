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
import { MatSnackBar } from '@angular/material';
import { Observable, BehaviorSubject } from "rxjs/Rx";
import * as SockJS from 'sockjs-client'

@Injectable()
export class DjdClientService {
    private debug: boolean = WEBPACK_ENV != 'production';
    private delimiter: string = 'ENDJSON\n';
    private connectionUrl: string = null;

    private reconnectInterval: number = 1000;
    private reconnectAttempts: number = 50;
    private isConnected: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(false);
    public isConnected$ = this.isConnected.asObservable();

    private sjsObservable: Observable<any> = null;
    private reconnectObservable: Observable<any> = null;
    private cmdId: number = 0;
    private sockJs: SockJS;
    private cmdCallbacks: any = {};
    private signals: Object = {}

    constructor(private snackbar: MatSnackBar) {}

    debugMsg(msg: string) {
        if (this.debug) {
            console.log(msg);
        }
    }

    init(url: string) {
        this.connectionUrl = url;
        this.connect()
    }

    connect() {
        this.sjsObservable = Observable.create((observer: any) => {
            this.debugMsg(`Sockjs -> connect to server ${this.connectionUrl}`);
            this.sockJs = new SockJS(this.connectionUrl);

            this.sockJs.onopen = (e: SockJS.OpenEvent) => {
                this.debugMsg('Sockjs -> connection to the server opened');
            };

            this.sockJs.onclose = (e: SockJS.CloseEvent) => {
                this.debugMsg("Sockjs -> connection close")
                this.isConnected.next(false);
                if (e.wasClean) {
                    observer.complete();
                } else {
                    observer.error(e);
                }
            };

            this.sockJs.onmessage = (e: MessageEvent) => {
                let msg: string = e.data;
                this.debugMsg(`Sockjs -> receive server message: ${msg}`);
                if (msg.indexOf("OK DEEJAYD") == 0) {
                    this.debugMsg("Socksjs -> Client Connected");
                    this.isConnected.next(true);
                } else if (msg.indexOf(this.delimiter) > 0) {
                    let answer: any = JSON.parse(msg.substr(0, msg.length - this.delimiter.length))
                    if (answer.hasOwnProperty("error") && answer.error != null) {
                        let err: string = ` ${answer.error.code} - ${answer.error.message}`;
                        if (this.cmdCallbacks.hasOwnProperty(answer.id)) {
                            this.cmdCallbacks[answer.id].error(err);
                        }
                    } else {
                        if (answer.result.type == "signal") {
                            let signal: any = answer.result.answer
                            if (this.signals.hasOwnProperty(signal.name)) {
                                this.signals[signal.name].forEach((cb: Function) => {
                                    cb(signal);
                                });
                            }
                        } else if (this.cmdCallbacks.hasOwnProperty(answer.id)) {
                            let value: any = this.formatAnswer(answer.result);
                            this.cmdCallbacks[answer.id].next(value);
                            this.cmdCallbacks[answer.id].complete();
                        }

                    }
                }
            }
        });

        this.sjsObservable.subscribe(
            null,
            (error: any) => {
                this.sjsObservable = null;
                if (this.reconnectObservable == null) {
                    this.debugMsg("An error ocurred in sockjs, try to reconnect")
                    // clean callbacks and signals and try to reconnect
                    this.cmdCallbacks = {};
                    this.signals = {};
                    this.reconnect();
                }
            }
        )
    }

    reconnect(): void {
        this.reconnectObservable = Observable.interval(this.reconnectInterval)
            .takeWhile((v, index) => {
                return index < this.reconnectAttempts && !this.sjsObservable;
            });
        this.reconnectObservable.subscribe(
            () => {
                this.debugMsg("New connection attempt");
                this.connect();
            },
            null,
            () => {
                this.reconnectObservable = null;
                if (!this.sjsObservable) {
                    this.debugMsg("Reconnection failed : max attemps are reached")
                    this.isConnected.complete();
                }
            });
    }

    formatAnswer(answer: any) : any {
        return answer.answer;
    }

    sendCommand(cmdName: string, args: Object): Observable<any> {
        if (this.isConnected.getValue()) {
            this.cmdId += 1;
            return Observable.create((observer: any) => {
                let cmd: Object = {
                    id: this.cmdId,
                    method: cmdName,
                    params: args,
                };
                this.debugMsg(`Send command ${JSON.stringify(cmd)}`)
                this.sockJs.send(JSON.stringify(cmd) + this.delimiter);
                this.cmdCallbacks[this.cmdId] = observer;
            });
        }
    }

    sendSimpleCmd(cmdName: string, args: Object): void {
        this.sendCommand(cmdName, args).subscribe((answer: any) => {
        }, (error: string) => {
            let snackBarRef = this.snackbar.open(error, "Close", {
                duration: 5000
            });
            snackBarRef.onAction().subscribe(() => {
                snackBarRef.dismiss();
            });
        })
    }

    subscribe(signal: string, callback: Function): void {
        if (!this.signals.hasOwnProperty(signal)) {
            this.signals[signal] = [];
            this.sendSimpleCmd('signal.setSubscription', [signal, true]);
        }
        this.signals[signal].push(callback);
    }

    unsubscribe(signal: string): void {
        if (this.signals.hasOwnProperty(signal)) {
            delete this.signals[signal]
            this.sendSimpleCmd('signal.setSubscription', [signal, false]);
        }
    }
}
