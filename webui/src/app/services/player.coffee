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

class DjdPlayerService
  constructor: (@djdclientservice, @$rootScope) ->
    @state = "stop"
    @volume = 0
    @time = 0
    @current_id = ""
    self = @

    @$rootScope.$on("djd:client:connected", (evt, data) ->
      self.djdclientservice.subscribe("player.status", (sig) ->
        self.updateStatus()
      )
      self.djdclientservice.subscribe("player.current", (sig) ->
        self.updateCurrent()
      )
      self.updateStatus()
      self.updateCurrent()
    )

  subscribeToSource: ->
    self = @
    @subscribe = () ->
      self.$rootScope.$broadcast("djd:player:current_id_changed", self.current_id)
      for key in ["audiopls", "audioqueue", "videopls"]
        @djdclientservice.subscribe("#{ key }.update", (sig) ->
          pl  = sig.name.split(".")[0]
          self.updatePlaylist(pl)
        )
        self.updatePlaylist(key)

    if @djdclientservice.is_connected
      @subscribe()
    else
      @$rootScope.$on("djd:client:connected", (evt, data) ->
        self.subscribe()
      )

  unsubscribeToSource: ->
    if @djdclientservice.is_connected
      for key in ["audiopls", "audioqueue", "videopls"]
        @djdclientservice.unsubscribe("#{ key }.update")

  updateStatus:  ->
    self = @
    @djdclientservice.sendCommand("player.getStatus", []).then((status) ->
      if status.state != self.state
        self.state = status.state
        self.$rootScope.$broadcast("djd:player:state_changed", self.state)

      if status.volume != self.volume
        self.volume = status.volume
        self.$rootScope.$broadcast("djd:player:volume_changed", self.volume)

      if status.time != self.time
        t = [0, 0]
        if status.time != undefined
          t = status.time.split(":")
        self.time = status.time
        self.$rootScope.$broadcast("djd:player:time_changed", {current: t[0], total: t[1]})

      c_id = ""
      if status.state != "stop"
        c_id = status.current
      if self.current_id != c_id
        self.current_id = c_id
        self.$rootScope.$broadcast("djd:player:current_id_changed", self.current_id)
    )

  updateCurrent: ->
    self = @
    @djdclientservice.sendCommand("player.getPlaying", []).then((answer) ->
      self.$rootScope.$broadcast("djd:player:playing_changed", answer)
    )

  updatePlaylist: (pls) ->
    self = @
    @djdclientservice.sendCommand("#{ pls }.getStatus", []).then((infos) ->
      self.$rootScope.$broadcast("djd:player:pls_updated", {pls: pls, infos: infos})
    )

  getState: ->
    return @state

  getVolume: ->
    return @volume

  goTo: (id, pls) ->
    @djdclientservice.sendCommand("player.goTo", [id, "id", pls])

  previous: ->
    @djdclientservice.sendCommand("player.previous", [])

  next: ->
    @djdclientservice.sendCommand("player.next", [])

  stop: ->
    @djdclientservice.sendCommand("player.stop", [])

  playToggle: ->
    @djdclientservice.sendCommand("player.playToggle", [])

  setVolume: (vol) ->
    @djdclientservice.sendCommand("player.setVolume", [vol])

  setVolumeRelative: (step) ->
    @djdclientservice.sendCommand("player.setVolumeRelative", [step])

  seek: (pos, relative=false) ->
    @djdclientservice.sendCommand("player.seek", [pos, relative])

  getAudioPlaylist: (start=0, length=null) ->
    args = [start]
    if length != null
      args.push(length)
    return @djdclientservice.sendCommand("audiopls.get", args)

  getAudioQueue: (start=0, length=null) ->
    args = [start]
    if length != null
      args.push(length)
    return @djdclientservice.sendCommand("audioqueue.get", args)

  getVideoPlaylist: (start=0, length=null) ->
    args = [start]
    if length != null
      args.push(length)
    return @djdclientservice.sendCommand("videopls.get", args)

  plsClear: (pls) ->
    @djdclientservice.sendCommand("#{ pls }.clear", [])

  plsShuffle: (pls) ->
    @djdclientservice.sendCommand("#{ pls }.shuffle", [])

  plsRemove: (pls, ids) ->
    @djdclientservice.sendCommand("#{ pls }.remove", [ids])

  plsOptions: (pls, option, value) ->
    @djdclientservice.sendCommand("#{ pls }.setOption", [option, value])

  audioPlsSave: (pls_name) ->
    return @djdclientservice.sendCommand("audiopls.save", [pls_name])

  getAvailableVideoOptions: () ->
    return @djdclientservice.setCommand("player.getAvailableVideoOptions")

  setVideoOption: (opts_name, opts_value) ->
    @djdclientservice.sendCommand("player.setVideoOption", [opts_name, opts_value])

DjdPlayerService.$inject = ["djdclientservice", "$rootScope"]
angular.module("djdWebui.player.services", [
  "djdWebui.services"
], ($provide) ->
  $provide.factory("djdplayerservice", (djdclientservice, $rootScope) ->
    return new DjdPlayerService(djdclientservice, $rootScope)
  )
)
