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

class DjdWebradioControl
  constructor: (@$scope, @alerts, @localize, @djdwebradioservice) ->
    self = @

    # init view vars
    @$scope.loading = false
    @$scope.activeSources = []
    @$scope.currentSource = {name: "", label: ""}
    @$scope.currentCategory = {name: "", id: -1}
    @$scope.hasMultipleSources = false
    @$scope.webradios = []
    @$scope.categories = []
    @$scope.view = 'category'
    # form input default value
    @$scope.categoryInputName = ""
    @$scope.webradioInputName = ""
    @$scope.webradioInputUrl = ""

    @$scope.setSource = (sName) ->
      if self.$scope.currentSource.name != sName
        for s in self.$scope.activeSources
          if s.name == sName
            self.$scope.currentSource = s
            self.$scope.view = 'category'
            self.updateCategoryList(sName)

    @$scope.getCategoriesList = ->
      self.updateCategoryList(self.$scope.currentSource.name)
    @$scope.getWebradioList = (sourceName, cat) ->
      self.updateWebradioList(sourceName, cat)

    @$scope.add = ->
      if self.$scope.view == 'webradio'
        if self.$scope.webradioInputUrl != "" && self.$scope.webradioInputName != ""
          self.djdwebradioservice.addWebradio(self.$scope.currentSource.name,
              self.$scope.currentCategory.id, self.$scope.webradioInputName,
              self.$scope.webradioInputUrl).then((result) ->
            $("#djd-modal-webradio-dialog").modal('hide')
            self.$scope.webradioInputName = ""
            self.$scope.webradioInputUrl = ""
          )
      else if self.$scope.view == 'category'
        self.djdwebradioservice.addCategory(self.$scope.currentSource.name,
                                            self.$scope.categoryInputName).then((result) ->
          $("#djd-modal-webradio-dialog").modal('hide')
          self.$scope.categoryInputName = ""
        )

    @$scope.clearWebradios = ->
      r = window.confirm(self.localize._("_clearWebradioConfirm_"))
      if r
        self.djdwebradioservice.clearWebradios(self.$scope.currentSource.name)

    @$scope.$on("djd:webradio:sourceListUpdated", (evt, sources) ->
      for s in sources
        self.$scope.activeSources.push({
          name: s.name,
          isEditable: s.editable,
          label: self.getLabel(s.name)
        })
      self.$scope.hasMultipleSources = sources.length > 1
      self.$scope.setSource(self.$scope.activeSources[0].name)
    )
    @$scope.$on("djd:webradio:listUpdated", (evt, sourceName) ->
      if sourceName == self.$scope.currentSource.name
        if self.$scope.view == 'category'
          self.updateCategoryList(sourceName)
        else if self.$scope.view == 'webradio'
          self.updateWebradioList(sourceName, self.$scope.currentCategory)
    )

    self.djdwebradioservice.connect()
    @$scope.$on('$destroy', ->
      self.djdwebradioservice.disconnect()
    )

  updateCategoryList: (sName) ->
    self = @
    @$scope.loading = true

    @djdwebradioservice.getCategories(sName).then((cats) ->
      self.$scope.view = 'category'

      self.$scope.webradios = []
      self.$scope.categories = cats
      self.$scope.loading = false
    )

  updateWebradioList: (sName, cat=null) ->
    self = @
    @$scope.loading = true

    @djdwebradioservice.getWebradios(sName, cat).then((wbs) ->
      self.$scope.currentCategory = cat
      self.$scope.view = 'webradio'

      self.$scope.categories = []
      self.$scope.webradios = wbs
      self.$scope.loading = false
    )

  getLabel: (source) ->
    labels = {
      "local": @localize._('_favorite_')
      "icecast": "Icecast"
    }
    if labels.hasOwnProperty(source) then labels[source] else source

DjdWebradioControl.$inject = ["$scope", "alerts", "localize", "djdwebradioservice"]

angular.module('djdWebui.webradio', [
  'djdWebui.alerts',
  'djdWebui.localization',
  'djdWebui.webradio.services',
  'ngRoute'
]).config(($routeProvider) ->
  $routeProvider
  .when('/radio', {
      templateUrl: 'gen/tpl/webradio.tpl.html',
      controller: 'DjdWebradioControl'
    });
).controller('DjdWebradioControl', DjdWebradioControl)
