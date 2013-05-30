# Deejayd, a media player daemon
# Copyright (C) 2007-2009 Mickael Royer <mickael.royer@gmail.com>
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

class DjdApp.PlayerController
  constructor: (@main_controller) ->
    # init var
    @is_loaded = false
    @is_pls_loaded = false
    @state = "stop"
    @volume = 0
    @rpc_client = @main_controller.client

  load: ->
    if not @is_loaded
      player_controller = @
      @view = new DjdApp.views.PlayerView(@)
      @updateCurrent()
      @updateStatus()

      # define event handlers
      @rpc_client.subscribe("player.status", (sig) ->
        player_controller.updateStatus()
      )
      @rpc_client.subscribe("player.current", (sig) ->
        player_controller.updateCurrent()
      )
      # load is finish
      @is_loaded = true

  loadPlaylist: ->
    if not @is_pls_loaded
      @pls_view = new DjdApp.views.PlaylistView(@)

      # define event handlers
      self = @
      for key in ["audiopls", "audioqueue", "videopls"]
        @rpc_client.subscribe("#{ key }.update", (sig) ->
          pl  = sig.name.split(".")[0]
          self.updatePlaylist(pl)
        )
        @updatePlaylist(key)

      @is_pls_loaded = true

  updatePlaylist: (pls) ->
    self = @
    @rpc_client.sendCommand("#{ pls }.getStatus", [], (infos) ->
      self.pls_view.refresh(pls, infos)
    )

  updateStatus:  ->
    _ref = @
    @rpc_client.sendCommand("player.getStatus", [], (status) ->
      if status.state != _ref.state
        _ref.view.updateState(status.state)
        _ref.state = status.state

      if status.volume != _ref.volume
        _ref.view.updateVolume(status.volume)
        _ref.volume = status.volume
    )

  updateCurrent: ->
    view = @view
    @rpc_client.sendCommand("player.getPlaying", [], (answer) ->
      view.refreshCurrent(answer)
    )
#
#  Commands called from view
#
  goTo: (id, pls) ->
    @rpc_client.sendCommand("player.goTo", [id, "id", pls])

  previous: ->
    @rpc_client.sendCommand("player.previous", [])

  next: ->
    @rpc_client.sendCommand("player.next", [])

  stop: ->
    @rpc_client.sendCommand("player.stop", [])

  playToggle: ->
    @rpc_client.sendCommand("player.playToggle", [])

  setVolume: (vol) ->
    @rpc_client.sendCommand("player.setVolume", [vol])

  getAudioPlaylist: (start=0, length=null, cb=null) ->
    args = [start]
    if length != null
      args.push(length)
    @rpc_client.sendCommand("audiopls.get", args, cb)

  getAudioQueue: (start=0, length=null, cb=null) ->
    args = [start]
    if length != null
      args.push(length)
    @rpc_client.sendCommand("audioqueue.get", args, cb)

  getVideoPlaylist: (start=0, length=null, cb=null) ->
    args = [start]
    if length != null
      args.push(length)
    @rpc_client.sendCommand("videopls.get", args, cb)

  plsClear: (pls) ->
    @rpc_client.sendCommand("#{ pls }.clear", [])

  plsShuffle: (pls) ->
    @rpc_client.sendCommand("#{ pls }.shuffle", [])

  plsRemove: (pls, ids) ->
    @rpc_client.sendCommand("#{ pls }.remove", [ids])

  plsOptions: (pls, option, value) ->
    @rpc_client.sendCommand("#{ pls }.setOption", [option, value])

# vim: ts=4 sw=4 expandtab
