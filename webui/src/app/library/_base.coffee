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

class _DjdBaseLibraryControl
  constructor: (@$scope, @alerts, @localize, @djdlibraryservice) ->
    self = @

    @$scope.currentView = "filesystem"
    # update vars and functions
    @$scope.reloadInProgress = false
    @$scope.reloadLibrary = ->
      self.djdlibraryservice.updateLibrary().then((result) ->
        self.$scope.reloadInProgress = true
      )
    @$scope.setCurrentView = (view) ->
      self.$scope.currentView = view


    # fs vars and functions
    @$scope.fsPath = ""
    @$scope.fsName = ""
    @$scope.fsBreadcrumbs = []
    @$scope.directories = []
    @$scope.files = []
    @$scope.loadFolder = (evt, path) ->
      self.loadFilesystem(path)

    @$scope.$on('djd:library:update', (evt) ->
      if self.$scope.reloadInProgress
        self.alerts.info(self.localize._('_libraryUpdated_'))
        self.$scope.reloadInProgress = false
      self.refresh()
    )

    @$scope.$on('$viewContentLoaded', ->
      self.djdlibraryservice.connect()
    )
    @$scope.$on('$destroy', ->
      self.djdlibraryservice.disconnect()
    )

  refresh: ->
    if @$scope.currentView == "filesystem"
      @loadFilesystem()

  loadFilesystem: (path='') ->
    self = @

    @djdlibraryservice.getFolderContent(path).then((answer) ->
      self.$scope.directories = answer.directories
      self.$scope.files = answer.files
    )
    @$scope.fsPath = path
    @$scope.current = 'filesystem'

    if path != ""
      # update breadcrumbs navigation
      parts = path.split("/")

      rel_path = ""
      @$scope.fsBreadcrumbs = [{path: "", name: " / "}]
      angular.forEach(parts, (p, idx) ->
        if idx < (parts.length-1)
          rel_path = self._pathJoin(rel_path, p)
          self.$scope.fsBreadcrumbs.push({name: p, path:rel_path})
        else
          self.$scope.fsName = p
      )

  _pathJoin: (paths...) ->
    index = null
    while (index = paths.indexOf("")) != -1
      paths.splice(index, 1);
    if paths.length > 0
      return paths.join("/")
    return ""

