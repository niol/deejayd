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
    @state = "stop"
    @volume = 0
    @rpc_client = @main_controller.client

  load: ->
    if not @is_loaded
      player_controller = @
      @view = new DjdApp.views.PlayerView(@)
      @updateCurrent()

      # define event handlers
      jQuery(document).on("djdStatusUpdate", (e, status) ->
        player_controller.updateStatus(status)
      )
      @rpc_client.subscribe("player.current", (sig) ->
        player_controller.updateCurrent()
      )
      # load is finish
      @is_loaded = true

  updateStatus: (status) ->
    if status.state != @state
      @view.updateState(status.state)
      @state = status.state

    if status.volume != @volume
      @view.updateVolume(status.volume)
      @volume = status.volume

  updateCurrent: ->
    view = @view
    @rpc_client.sendCommand("player.getPlaying", [], (answer) ->
      view.refreshCurrent(answer.answer)
    )
#
#  Commands called from view
#
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

# vim: ts=4 sw=4 expandtab
