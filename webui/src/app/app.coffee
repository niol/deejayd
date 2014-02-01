# Deejayd, a media player daemon
# Copyright (C) 2013 Mickael Royer <mickael.royer@gmail.com>
#                    Alexandre Rossi <alexandre.rossi@gmail.com>
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

class DjdMainCtrl
  constructor: (@$scope, @$location, @localize, @djdclientservice) ->
    # init deejayd client
    deejayd_root_url = DjdApp.options.root_url
    rpc_url = "http://#{location.host}#{deejayd_root_url}rpc/"

    self = @
    @$scope.loading = true
    @$scope.loadingMsg = @localize._('_connection_')
    self.$scope.location = "/"
    @$scope.$on("$locationChangeStart", (evt, newUrl, oldUrl) ->
      self.$scope.location = self.$location.path()
    )

    @$scope.$on("djd:client:connected", (evt) ->
      self.$scope.loading = false
      self.$scope.$apply()
    )
    @$scope.$on("djd:client:closed", (evt) ->
      self.$scope.loadingMsg = self.localize._('_connectionLost_')
      self.$scope.loading = true
      self.$scope.$apply()
    )
    @djdclientservice.connect(rpc_url)

DjdMainCtrl.$inject = ["$scope", "$location", "localize", "djdclientservice"]
angular.module("djdWebui", [
  'ngRoute',
  'djdWebui.localization',
  'djdWebui.alerts',
  'djdWebui.widgets',
  'djdWebui.services'
  'djdWebui.player'
  'djdWebui.sourcePlaylist'
  'djdWebui.library.music'
  'djdWebui.library.video'
  'djdWebui.webradio'
]).controller("DjdMainCtrl", DjdMainCtrl)