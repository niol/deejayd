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

class DjdApp.PlayerController extends DjdApp.BaseController
  constructor: (@main_controller) ->
    super(@main_controller)

    # init var
    @is_pls_loaded = false
    @state = "stop"
    @volume = 0
    @time = 0

  load: ->
    if not @is_loaded
      self = @
      if DjdApp.options.ui == "mobile"
        @view = new DjdApp.views.MobilePlayerView(@)
      else if DjdApp.options.ui == "desktop"
        @view = new DjdApp.views.DesktopPlayerView(@)
      @updateCurrent()
      @updateStatus()

      # define event handlers
      @rpc_client.subscribe("player.status", (sig) ->
        self.updateStatus()
      )
      @rpc_client.subscribe("player.current", (sig) ->
        self.updateCurrent()
      )
      # load is finish
      @is_loaded = true
    @view.load()

  loadPlaylist: ->
    if not @is_pls_loaded
      if DjdApp.options.ui == "mobile"
        @pls_view = new DjdApp.views.MobilePlaylistView(@)
      else if DjdApp.options.ui == "desktop"
        @pls_view = new DjdApp.views.DesktopPlaylistView(@)

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
    self = @
    @rpc_client.sendCommand("player.getStatus", [], (status) ->
      if status.state != self.state
        self.view.updateState(status.state)
        self.state = status.state

      if status.volume != self.volume
        self.view.updateVolume(status.volume)
        self.volume = status.volume

      if status.time != self.time
        t = [0, 0]
        if status.time != undefined
          t = status.time.split(":")
        self.view.updateTime(t[0], t[1])
        self.time = status.time
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

  seek: (pos, relative=false) ->
    @rpc_client.sendCommand("player.seek", [pos, relative])

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

  audioPlsSave: (pls_name, cb) ->
    @rpc_client.sendCommand("audiopls.save", [pls_name], cb)

# vim: ts=4 sw=4 expandtab