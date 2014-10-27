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
  constructor: (@$http, @$rootScope, @$window, @$q, @$log) ->
    @language = @$window.navigator.userLanguage || @$window.navigator.language
    @resourceFileLoaded = false
    @dictionary = {}

  initLocalizedResources: ->
    self = @
    deferred = @$q.defer();

    url = 'i18n/djdwebui-locale_' + @language + '.json';
    @$http({ method:"GET", url:url, cache:false }).success((data) ->
      deferred.resolve(data)
    ).error( ->
        url = 'i18n/djdwebui-locale_default.json'
        self.$http({ method:"GET", url:url, cache:false }).success((data) ->
          deferred.resolve(data)
        ).error( ->
          deferred.resolve({})
        )
    )
    deferred.promise

  getLocalizedString: (key) ->
    if (!@resourceFileLoaded)
      @resourceFileLoaded = true
      self = @
      promise = @initLocalizedResources()
      promise.then((dict) ->
        self.dictionary = dict
        self.$rootScope.$emit('djd:localize:resourcesUpdates')
      )
      return key

    if @dictionary.hasOwnProperty(key)
      return @dictionary[key]
    return key

  _: (key) -> # shortcut
    return @getLocalizedString(key)

module = angular.module("djdWebui.localization", [ ], ($provide) ->
  $provide.factory("localize", ['$http', '$rootScope', '$window', '$q', '$log', ($http, $rootScope, $window, $q, $log) ->
    return new DjdLocalization($http, $rootScope, $window, $q, $log)
  ])
).filter('i18n', ['localize', (localize) ->
  filterFunc = (input) ->
    return localize.getLocalizedString(input)

  filterFunc.$stateful = true
  return filterFunc
])
