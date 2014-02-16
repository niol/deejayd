# Deejayd, a media player daemon
# Copyright (C) 2007-2014 Mickael Royer <mickael.royer@gmail.com>
#                         Alexandre Rossi <alexandre.rossi@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

class DjdMusicLibraryControl extends _DjdBaseLibraryControl
  constructor: (@$scope, @alerts, @localize, @djdmusiclibraryservice) ->
    super(@$scope, @alerts, @localize, @djdmusiclibraryservice)

DjdMusicLibraryControl.$inject = ["$scope", "alerts", "localize", "djdmusiclibraryservice"]

musicModule = angular.module('djdWebui.library.music', [
  'djdWebui.alerts',
  'djdWebui.localization',
  'djdWebui.library.services',
  'ngRoute'
]).config(($routeProvider) ->
  $routeProvider
  .when('/music', {
      templateUrl: 'gen/tpl/music.tpl.html',
      controller: 'DjdMusicLibraryControl'
    });
).controller('DjdMusicLibraryControl', DjdMusicLibraryControl)
 .filter("audiotag", ["localize", (localize) ->
  (tag) ->
    if tag == ''
      tag = "<em>#{ localize._('_unknown_') }</em>"
    return tag
])


class DjdAudioTagNavigationCtrl
  constructor: (@tagName, @$scope, @localize, @djdmusiclibraryservice) ->
    self = @
    @$scope.activeView = {
      type: @tagName
    }
    @$scope.tagList = []
    @$scope.albumList = []

    @$scope.loadAlbums = (tagname, tag) ->
      filter = new DjdApp.models.MediaBasicFilter("equals", tagname, tag)
      self.djdmusiclibraryservice.getAlbum(filter).then((albums) ->
        self.$scope.activeView.type = 'album'
        self.$scope.albumList = albums

        self.$scope.activeView.label = tag
        self.$scope.activeView.backLabel = self.localize._("_#{self.tagName}List_")
      )
    @$scope.goBack = ->
      if self.$scope.activeView.type == 'album'
        self.loadTagList()
    @loadTagList()


  loadTagList: ->
    self = @
    @djdmusiclibraryservice.getTagList(self.tagName).then((tList) ->
      self.$scope.activeView.type = self.tagName
      self.$scope.tagList = tList
    )

class DjdGenreNavigationCtrl extends DjdAudioTagNavigationCtrl
  constructor: (@$scope, @localize, @djdmusiclibraryservice) ->
    super('genre', @$scope, @localize, @djdmusiclibraryservice)
DjdGenreNavigationCtrl.$inject = ["$scope", "localize", "djdmusiclibraryservice"]

class DjdArtistNavigationCtrl extends DjdAudioTagNavigationCtrl
  constructor: (@$scope, @localize, @djdmusiclibraryservice) ->
    super('artist', @$scope, @localize, @djdmusiclibraryservice)
DjdArtistNavigationCtrl.$inject = ["$scope", "localize", "djdmusiclibraryservice"]

class DjdAlbumNavigationCtrl
  constructor: (@$scope, @localize, @djdmusiclibraryservice) ->
    @$scope.albumList = []

    self = @
    @djdmusiclibraryservice.getAlbum(null).then((albums) ->
      self.$scope.albumList = albums
    )
DjdAlbumNavigationCtrl.$inject = ["$scope", "localize", "djdmusiclibraryservice"]

musicModule.controller('DjdGenreNavigationCtrl', DjdGenreNavigationCtrl)
musicModule.controller('DjdArtistNavigationCtrl', DjdArtistNavigationCtrl)
musicModule.controller('DjdAlbumNavigationCtrl', DjdAlbumNavigationCtrl)
