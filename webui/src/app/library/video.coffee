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

class DjdVideoLibraryControl extends _DjdBaseLibraryControl
  constructor: (@$scope, @alerts, @localize, @djdvideolibraryservice) ->
    super(@$scope, @alerts, @localize, @djdvideolibraryservice)

    # search
    self = @
    @$scope.searchModel = {
      input: ""
      resultVisible: false
      resultPatern: ""
      results: []
    }
    @$scope.search = (input) ->
      if input != ""
        filter = new DjdApp.models.MediaBasicFilter("contains", "title", input)
        self.djdvideolibraryservice.search(filter).then((mList) ->
          self.$scope.searchModel.resultVisible = true
          self.$scope.searchModel.resultPattern = input
          self.$scope.searchModel.input = ""

          self.$scope.searchModel.results = mList
        )


DjdVideoLibraryControl.$inject = ["$scope", "alerts", "localize", "djdvideolibraryservice"]

angular.module('djdWebui.library.video', [
  'djdWebui.alerts',
  'djdWebui.localization',
  'djdWebui.library.services',
  'ngRoute'
]).config(($routeProvider) ->
  $routeProvider
  .when('/video', {
      templateUrl: 'gen/tpl/video.tpl.html',
      controller: 'DjdVideoLibraryControl'
    });
).controller('DjdVideoLibraryControl', DjdVideoLibraryControl)