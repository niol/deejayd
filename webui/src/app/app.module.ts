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
// angular imports

import { NgModule } from '@angular/core';
import { RouterModule } from '@angular/router';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';

// modules and providers for flex-layout
import { FlexLayoutModule } from '@angular/flex-layout';
import {DEFAULT_BREAKPOINTS_PROVIDER, BreakPointRegistry, MatchMedia,
        OBSERVABLE_MEDIA_PROVIDER} from '@angular/flex-layout';

// material styles and components
import "../../node_modules/@angular/material/prebuilt-themes/indigo-pink.css";
import { MatSidenavModule, MatToolbarModule,
         MatButtonModule, MatIconModule, MatButtonToggleModule,
         MatSliderModule, MatTabsModule, MatListModule,
         MatMenuModule, MatDialogModule, MatSnackBarModule,
         MatSelectModule, MatInputModule, MatProgressSpinnerModule } from '@angular/material';

// app custom styles
import "../styles/custom.css"
// app component
import { AppComponent } from './app.component';
import { PlayerComponent } from './components/player/player.component';
import { VolumeComponent } from './components/player/volume.component';
import { PlayingQueuesComponent } from './components/playing-queues.component'
import { PlaylistComponent } from './components/playlist.component';
import { MusicLibraryComponent } from './components/library/music-library.component';
import { VideoLibraryComponent } from './components/library/video-library.component';
import { FolderViewComponent } from './components/library/folder-view.component';
import { SearchViewComponent } from './components/library/search-view.component';
import { VideoOptionsDialog } from './components/player/options-dialog.component';
import { SeekDialogComponent } from './components/player/seek-dialog.component';
import { WebradioComponent } from './components/webradio/webradio.component';
import { WebradioSourceComponent } from './components/webradio/webradio-source.component';
import { WrCategoryDialogComponent } from './components/webradio/category-dialog.component';
import { WebradioDialogComponent } from './components/webradio/webradio-dialog.component';
import { ConfirmDialogComponent } from './components/common/confirm-dialog.component';
// app services
import { DjdClientService } from './services/djd-client.service'
import { PlayerService } from './services/player.service';
import { MenuService } from './services/menu.service';
import { UtilsService } from './services/utils.service';
import { WebradioService } from './services/webradio.service';
// app routes
import { appRoutes } from './app.routes';

@NgModule({
  declarations: [
    AppComponent,
    PlayerComponent,
    VolumeComponent,
    PlayingQueuesComponent,
    PlaylistComponent,
    MusicLibraryComponent,
    VideoLibraryComponent,
    FolderViewComponent,
    SearchViewComponent,
    VideoOptionsDialog,
    SeekDialogComponent,
    WebradioComponent,
    WebradioSourceComponent,
    ConfirmDialogComponent,
    WrCategoryDialogComponent,
    WebradioDialogComponent
  ],
  entryComponents: [
    VideoOptionsDialog,
    SeekDialogComponent,
    ConfirmDialogComponent,
    WrCategoryDialogComponent,
    WebradioDialogComponent
  ],
  imports: [
    RouterModule.forRoot(appRoutes),
    BrowserModule,
    FormsModule,
    BrowserAnimationsModule,
    FlexLayoutModule,
    MatToolbarModule,
    MatSidenavModule,
    MatButtonModule,
    MatButtonToggleModule,
    MatIconModule,
    MatSliderModule,
    MatTabsModule,
    MatListModule,
    MatMenuModule,
    MatDialogModule,
    MatSelectModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatSnackBarModule
  ],
  providers: [
    DEFAULT_BREAKPOINTS_PROVIDER,
    BreakPointRegistry,
    MatchMedia,
    OBSERVABLE_MEDIA_PROVIDER,
    DjdClientService,
    PlayerService,
    MenuService,
    UtilsService,
    WebradioService
  ],
  bootstrap: [ AppComponent ],
})
export class AppModule {}
