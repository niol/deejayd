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

class DjdFileCtrl
  constructor: (@$scope, @djdmusiclibraryservice, @djdvideolibraryservice) ->
    self = @

    @library = if @$scope.file.type == 'song' then @djdmusiclibraryservice else @djdvideolibraryservice
    @filter = new DjdApp.models.MediaBasicFilter("equals", "id", @$scope.file.media_id)
    @$scope.playFile = () ->
      self.library.play(self.filter)

    @$scope.addFileToPls = () ->
      self.library.addToPls(self.filter)

    @$scope.addFileToQueue = () ->
      self.library.addToQueue(self.filter)

angular.module('djdWebui.widgets')
.directive('djdFile', () ->
    restrict: 'A',
    scope: {
      fileNo: '=',
      file: '='
    },
    replace: false,
    templateUrl: 'gen/tpl/file.tpl.html'
    controller: ['$scope', 'djdmusiclibraryservice', 'djdvideolibraryservice', DjdFileCtrl]
  )

class DjdFolderCtrl
  constructor: (@$scope, @djdmusiclibraryservice, @djdvideolibraryservice) ->
    self = @

    @library = if @$scope.libraryType == 'music' then @djdmusiclibraryservice else @djdvideolibraryservice
    @$scope.playFile = () ->
      self.library.play([self.$scope.folder.id], type='folder')

    @$scope.addFileToPls = () ->
      self.library.addToPls([self.$scope.folder.id], type='folder')

    @$scope.addFileToQueue = () ->
      self.library.addToQueue([self.$scope.folder.id], type='folder')

angular.module('djdWebui.widgets')
.directive('djdFolder', () ->
    restrict: 'A',
    scope: {
      folder: '='
      loadFolder: '='
      folderNo: '='
      libraryType: '='
    },
    replace: false,
    templateUrl: 'gen/tpl/folder.tpl.html'
    controller: ['$scope', 'djdmusiclibraryservice', 'djdvideolibraryservice', DjdFolderCtrl]
  )

class DjdAudioTagCtrl
  constructor: (@$scope, @djdmusiclibraryservice) ->
    self = @

    @library = @djdmusiclibraryservice
    @$scope.play = () ->
      filter = new DjdApp.models.MediaBasicFilter("equals", self.$scope.tagname, self.$scope.tag)
      self.library.play(filter, type='filter')

    @$scope.addToPls = () ->
      filter = new DjdApp.models.MediaBasicFilter("equals", self.$scope.tagname, self.$scope.tag)
      self.library.addToPls(filter, type='filter')

    @$scope.addToQueue = () ->
      filter = new DjdApp.models.MediaBasicFilter("equals", self.$scope.tagname, self.$scope.tag)
      self.library.addToQueue(filter, type='filter')

angular.module('djdWebui.widgets')
.directive('djdAudiotag', () ->
    restrict: 'A',
    scope: {
      tagname: '='
      loadAlbums: '='
      tag: '='
    },
    replace: false,
    templateUrl: 'gen/tpl/audiotag.tpl.html'
    controller: ['$scope', 'djdmusiclibraryservice', DjdAudioTagCtrl]
  )

class DjdAlbumCtrl
  constructor: (@$scope, @djdmusiclibraryservice) ->
    self = @

    @library = @djdmusiclibraryservice
    @$scope.getCoverUrl = (album) ->
      if album.cover_filename != ""
        return "covers/#{ album.cover_filename }"
      return "images/missing-cover.png"
    @$scope.play = () ->
      filter = new DjdApp.models.MediaBasicFilter("equals", 'album', self.$scope.album.name)
      self.library.play(filter, type='filter')

    @$scope.addToPls = () ->
      filter = new DjdApp.models.MediaBasicFilter("equals", 'album', self.$scope.album.name)
      self.library.addToPls(filter, type='filter')

    @$scope.addToQueue = () ->
      filter = new DjdApp.models.MediaBasicFilter("equals", 'album', self.$scope.album.name)
      self.library.addToQueue(filter, type='filter')

angular.module('djdWebui.widgets')
.directive('djdAlbum', () ->
    restrict: 'A',
    scope: {
      album: '='
    },
    replace: false,
    templateUrl: 'gen/tpl/album.tpl.html'
    controller: ['$scope', 'djdmusiclibraryservice', DjdAlbumCtrl]
  )
