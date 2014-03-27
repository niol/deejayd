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


class _DjdBaseLibraryService
  constructor: (@djdclientservice, @$rootScope) ->
    self = @

  connect: ->
    self = @
    @subscribe = () ->
      self.djdclientservice.subscribe("mediadb.#{self.signal}", (sig) ->
        self.$rootScope.$broadcast("djd:library:update")
      )
      self.$rootScope.$broadcast("djd:library:update")
    if @djdclientservice.is_connected
      @subscribe()
    else
      @$rootScope.$on("djd:client:connected", (evt, data) ->
        self.subscribe()
      )

  disconnect: ->
    if @djdclientservice.is_connected
      @djdclientservice.unsubscribe("mediadb.#{@signal}")

  getLibraryType: ->
    return ""

  getFolderContent: (folder='') ->
    @djdclientservice.sendCommand("#{ @getLibraryType() }lib.getDirContent", [folder])

  search: (filter) ->
    filter = filter.dump() if filter != null
    @djdclientservice.sendCommand("#{ @getLibraryType() }lib.search", [filter])

  updateLibrary: ->
    @djdclientservice.sendCommand("#{ @getLibraryType() }lib.update", [])

  play: (value, type="filter", position=0) ->
    cmd = "loadFolders"
    if type == "filter"
      value = value.dump() if value != null
      cmd = "addMediaByFilter"

    pls = "#{ @getLibraryType() }pls"
    @djdclientservice.sendCommand("#{ pls }.#{ cmd }", [value, false]).then( (ans) =>
      @djdclientservice.sendCommand("player.goTo", [0, "pos", pls]).then( (ans) =>
        if position
          @djdclientservice.sendCommand("player.seek", [position])
      )
    )

  addToPls: (value, type="filter") ->
    cmd = "loadFolders"
    if type == "filter"
      value = value.dump() if value != null
      cmd = "addMediaByFilter"
    @djdclientservice.sendCommand("#{ @getLibraryType() }pls.#{ cmd }", [value, true])

class DjdMusicLibraryService extends _DjdBaseLibraryService
  constructor: (@djdclientservice, @$rootScope) ->
    super(@djdclientservice, @$rootScope)
    @signal = "aupdate"

  getLibraryType: ->
    return "audio"

  addToQueue: (value, type="filter") ->
    cmd = "loadFolders"
    if type == "filter"
      value = value.dump() if value != null
      cmd = "addMediaByFilter"
    @djdclientservice.sendCommand("audioqueue.#{ cmd }", [value, true])

  setRating: (filter, value) ->
    filter = filter.dump() if filter != null
    @djdclientservice.sendCommand("audiolib.setRating", [filter, value])

  getTagList: (tagName) ->
    @djdclientservice.sendCommand("audiolib.tagList", [tagName])

  getAlbum: (filter) ->
    filter = filter.dump() if filter != null
    @djdclientservice.sendCommand("audiolib.albumList", [filter])

  getSongs: (filter) ->
    filter = filter.dump() if filter != null
    @djdclientservice.sendCommand("audiolib.search", [filter])
DjdMusicLibraryService.$inject = ["djdclientservice", "$rootScope"]


class DjdVideoLibraryService extends _DjdBaseLibraryService
  constructor: (@djdclientservice, @$rootScope) ->
    super(@djdclientservice, @$rootScope)
    @signal = "vupdate"

  getLibraryType: ->
    return "video"
DjdVideoLibraryService.$inject = ["djdclientservice", "$rootScope"]

angular.module("djdWebui.library.services", [
  "djdWebui.services"
], ($provide) ->
  $provide.factory("djdmusiclibraryservice", (djdclientservice, $rootScope) ->
    return new DjdMusicLibraryService(djdclientservice, $rootScope)
  )
  $provide.factory("djdvideolibraryservice", (djdclientservice, $rootScope) ->
    return new DjdVideoLibraryService(djdclientservice, $rootScope)
  )
)
