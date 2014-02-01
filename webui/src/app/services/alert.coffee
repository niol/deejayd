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

class DjdAlertService
  constructor: (@$rootScope) ->
    self = @
    @$rootScope.$on("djd:client:error", (evt, err) ->
      self.error("Error: #{err}")
    )

  _msg: (msg, type) ->
    @$rootScope.$broadcast("djd:alert:new", {
      msg: msg
      type: type
    })

  info: (msg) ->
    @_msg(msg, 'info')

  error: (msg) ->
    @_msg(msg, 'error')

module = angular.module("djdWebui.alerts", [ ], ($provide) ->
  $provide.factory("alerts", ['$rootScope', ($rootScope) ->
    return new DjdAlertService($rootScope)
  ])
)
