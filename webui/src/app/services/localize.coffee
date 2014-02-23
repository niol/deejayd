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

class DjdLocalization
  constructor: (@$http, @$rootScope, @$window, @$filter) ->
    @language = @$window.navigator.userLanguage || @$window.navigator.language
    @dictionary = {}
    @resourceFileLoaded = false

  initLocalizedResources: ->
    self = @

    url = 'i18n/djdwebui-locale_' + @language + '.json';
    console.log url
    @$http({ method:"GET", url:url, cache:false }).success((data) ->
      self.successCallback(data)
    ).error( ->
        url = 'i18n/djdwebui-locale_default.json'
        self.$http({ method:"GET", url:url, cache:false }).success((data) ->
          self.successCallback(data)
        )
    )

  getLocalizedString: (key) ->
    if (!@resourceFileLoaded)
      @initLocalizedResources()
      @resourceFileLoaded = true
      return key

    if @dictionary.hasOwnProperty(key)
      return @dictionary[key]
    return key

  _: (key) -> # shortcut
    return @getLocalizedString(key)

  successCallback:(data) ->
    @dictionary = data
    @resourceFileLoaded = true
    @$rootScope.$broadcast('djd:localize:resourcesUpdates')

module = angular.module("djdWebui.localization", [ ], ($provide) ->
  $provide.factory("localize", ['$http', '$rootScope', '$window', '$filter', ($http, $rootScope, $window, $filter) ->
    return new DjdLocalization($http, $rootScope, $window, $filter)
  ])
).filter('i18n', ['localize', (localize) ->
  (input) ->
    return localize.getLocalizedString(input)
])
