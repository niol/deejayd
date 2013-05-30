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

class DjdApp.AudioLibraryController
  constructor: (@main_controller) ->
    # init var
    @is_loaded = false
    @rpc_client = @main_controller.client

  load: ->
    if not @is_loaded
      @is_loaded = true
      @view =  new DjdApp.views.AudioLibraryView(@)

      # define event handlers
      _ref = @
      @rpc_client.subscribe("mediadb.aupdate", (sig) ->
        _ref.view.refresh()
      )

#
#  Commands called from view
#
  getFolderContent: (folder='', cb) ->
    @rpc_client.sendCommand("audiopls.getDirContent", [folder], cb)

  playByFilter: (filter) ->
    filter = filter.dump() if filter != null
    self = @
    @rpc_client.sendCommand("audiopls.addMediaByFilter", [filter, false], (ans) ->
      self.rpc_client.sendCommand("player.goTo", [0, "pos", "audiopls"])
    )

  addByFilter: (filter) ->
    filter = filter.dump() if filter != null
    self = @
    @rpc_client.sendCommand("audiopls.addMediaByFilter", [filter, true])

  addQueueByFilter: (filter) ->
    filter = filter.dump() if filter != null
    self = @
    @rpc_client.sendCommand("audioqueue.addMediaByFilter", [filter, true])

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
