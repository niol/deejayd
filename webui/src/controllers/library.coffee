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

class DjdApp.LibraryController
  constructor: (@main_controller) ->
    # init var
    @signal = ''
    @type = ''
    @is_loaded = false
    @rpc_client = @main_controller.client

  load: ->
    if not @is_loaded
      @is_loaded = true
      @view =  @initView()

      # define event handlers
      @rpc_client.subscribe("mediadb.#{ @signal }", (sig) =>
        @view.refresh()
      )

  initView: ->
    return null

  getFolderContent: (folder='', cb) ->
    @rpc_client.sendCommand("#{ @type }lib.getDirContent", [folder], cb)

#
#  Commands called from view
#
  play: (value, type="filter") ->
    cmd = "loadFolders"
    if type == "filter"
      value = value.dump() if value != null
      cmd = "addMediaByFilter"

    pls = "#{ @type }pls"
    @rpc_client.sendCommand("#{ pls }.#{ cmd }", [value, false], (ans) =>
      @rpc_client.sendCommand("player.goTo", [0, "pos", pls])
    )

  addToPls: (value, type="filter") ->
    cmd = "loadFolders"
    if type == "filter"
      value = value.dump() if value != null
      cmd = "addMediaByFilter"
    @rpc_client.sendCommand("#{ @type }pls.#{ cmd }", [value, true])


class DjdApp.AudioLibraryController extends DjdApp.LibraryController
  constructor: (@main_controller) ->
    super(@main_controller)
    @signal = "aupdate"
    @type = "audio"

  initView: ->
    return new DjdApp.views.AudioLibraryView(@)

#
#  Commands called from view
#
  addToQueue: (value, type="filter") ->
    cmd = "loadFolders"
    if type == "filter"
      value = value.dump() if value != null
      cmd = "addMediaByFilter"
    @rpc_client.sendCommand("audioqueue.#{ cmd }", [value, true])

  setRating: (filter, value) ->
    filter = filter.dump() if filter != null
    @rpc_client.sendCommand("audiolib.setRating", [filter, value])

  getGenre: (cb) ->
    @rpc_client.sendCommand("audiolib.tagList", ["genre"], cb)

  getArtist: (cb) ->
    @rpc_client.sendCommand("audiolib.tagList", ["artist"], cb)

  getAlbum: (filter, cb) ->
    filter = filter.dump() if filter != null
    @rpc_client.sendCommand("audiolib.albumList", [filter], cb)

  getSongs: (filter, cb) ->
    filter = filter.dump() if filter != null
    @rpc_client.sendCommand("audiolib.search", [filter], cb)


class DjdApp.VideoLibraryController extends DjdApp.LibraryController
  constructor: (@main_controller) ->
    super(@main_controller)
    @signal = "vupdate"
    @type = "video"

  initView: ->
    return new DjdApp.views.VideoLibraryView(@)
