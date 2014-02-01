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

class DjdWebradioCtrl
  constructor: (@$scope, @localize, @djdwebradioservice) ->
    self = @
    @$scope.play = ->
      self.djdwebradioservice.playWebradio(self.$scope.webradio.get('wb_id'))

    @$scope.erase = ->
      r = window.confirm(self.localize._("_eraseWebradioConfirm_"))
      if r
        self.djdwebradioservice.eraseWebradio(self.$scope.source.name,
                                              self.$scope.webradio.get('wb_id'))

class DjdWbCategoryCtrl
  constructor: (@$scope, @localize, @djdwebradioservice) ->
    self = @

    @$scope.erase = ->
      r = window.confirm(self.localize._("_eraseCategoryConfirm_"))
      if r
        self.djdwebradioservice.eraseCategory(self.$scope.source.name,
                                              self.$scope.category.id)

angular.module('djdWebui.widgets')
.directive('djdWebradio', () ->
    restrict: 'A',
    scope: {
      webradio: '='
      isEditable: '='
      source: '='
    },
    replace: false,
    templateUrl: 'gen/tpl/webradio-entry.tpl.html'
    controller: ['$scope', "localize", 'djdwebradioservice', DjdWebradioCtrl]
  )
.directive('djdWbcat', () ->
    restrict: 'A',
    scope: {
      category: '='
      getWebradio: '='
      isEditable: '='
      source: '='
    },
    replace: false,
    templateUrl: 'gen/tpl/webradio-category.tpl.html'
    controller: ['$scope', "localize", 'djdwebradioservice', DjdWbCategoryCtrl]
  )
