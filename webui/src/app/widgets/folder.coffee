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