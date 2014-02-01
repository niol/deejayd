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

class DjdAlertsCtrl
  constructor: (@$scope, @$timeout) ->
    @id = 1
    self = @
    @$scope.alerts = {}
    @$scope.remove = (id) ->
      if !id then id = self.id
      if self.$scope.alerts.hasOwnProperty(id)
        delete self.$scope.alerts[id]

    @$scope.$on("djd:alert:new", (evt, alert) ->
      self.$scope.alerts[self.getId()] = {
        type: alert.type
        msg: alert.msg
      }
      if alert.type != 'error'
        self.$timeout(self.$scope.remove, 3000)

      self.$scope.$apply(() ->
        window.scrollTo(0, 0)
      )
    )

  getId: ->
    @id += 1
    return @id

angular.module('djdWebui.widgets')
.directive('djdAlerts', () ->
    restrict: 'A',
    scope: { },
    replace: false,
    templateUrl: 'gen/tpl/alerts.tpl.html'
    controller: ['$scope', "$timeout", DjdAlertsCtrl]
  )
