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

class DjdTrackCtrl
  constructor: (@$scope, @djdplayerservice) ->
    self = @
    @$scope.playTrack = (position=0) ->
      self.djdplayerservice.goTo(self.$scope.track.id, self.$scope.pls, position)

    @$scope.removeTrack = () ->
      self.djdplayerservice.plsRemove(self.$scope.pls, [self.$scope.track.id])

angular.module('djdWebui.widgets')
.directive('djdTrack', (util) ->
  restrict: 'A',
  scope: {
    trackNo: '=',
    track: '='
    pls: '='
  },
  replace: false,
  templateUrl: 'gen/tpl/track.tpl.html'
  controller: ['$scope', 'djdplayerservice', DjdTrackCtrl]
  link: (scope, element, attrs) ->
    scope.util = util
    scope.desc = ""
    if scope.track.type == "song"
      scope.desc = "#{ scope.track['artist'] } - #{ scope.track['album'] }"
    else if scope.track.type == "video"
      scope.desc = if scope.track['external_subtitle'] == "" then "Without subtitle" else "With subtitle"

    scope.$on('$destroy', () ->
      return
    )
)