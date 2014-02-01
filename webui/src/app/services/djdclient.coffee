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

class DjdWebClient
  delimiter: 'ENDJSON\n'

  constructor: (@$q, @$rootScope, @$log) ->
    @connection_try = 0
    @reconnecting = false
    @is_connected = false

  init: ->
    @cmd_id = 0
    @cmd_callbacks = {}
    @signals = {}

  on_open: ->
    @$log.debug "Connection to server open"
    @is_connected = true
    @reconnecting = false

  on_message: (msg) ->
    @$log.debug("Receive server message: #{msg}")

    self = @
    if msg.indexOf("OK DEEJAYD") == 0
      self.is_connected = true
      self.$rootScope.$broadcast('djd:client:connected');
    else if msg.indexOf(self.delimiter) > 0
      answer = JSON.parse(msg.substr(0, msg.length-self.delimiter.length))
      if answer.error # some errors happen, display a message
        err = "#{ answer.error.code } - #{ answer.error.message }"
        self.$rootScope.$broadcast("djd:client:error", err)
        if self.cmd_callbacks.hasOwnProperty(answer.id)
          deferred = self.cmd_callbacks[answer.id]
          deferred.reject(err)
      else
        if answer.result.type == "signal" # we receive signal dispatch it
          signal = answer.result.answer
          if self.signals.hasOwnProperty(signal.name)
            for cb in self.signals[signal.name]
              cb(signal)

        else if self.cmd_callbacks.hasOwnProperty(answer.id)
          deferred = self.cmd_callbacks[answer.id]
          deferred.resolve(self._formatAnswer(answer.result))

  connect: (@url) ->
    @_connect()

  _connect: ->
    @init()

    self = @
    @sock = new SockJS(@url);
    @sock.onopen = ->
      self.on_open()

    @sock.onmessage = (e) ->
      self.on_message(e.data)

    @sock.onclose = ->
      if !self.reconnecting
        self.$log.debug "Connection to server close"
        self.$rootScope.$broadcast('djd:client:closed');
      self.is_connected = false

      # try to reconnect
      setTimeout(() ->
        self.reconnecting = true
        self._connect()
      , 2000 * self.connection_try)
      self.connection_try += 1


  _formatAnswer: (answer) ->
    switch answer.type
      when "media"
        if answer.answer != null
          return new DjdApp.models.Media(answer.answer)
        return null
      when "medialist"
        return new DjdApp.models.MediaList(answer.answer)
      when "playlist"
        return new DjdApp.models.Playlist(answer.answer)
      else
        return answer.answer

  sendCommand: (cmd_name, args) ->
    deferred = @$q.defer()
    if @is_connected
      @cmd_id += 1
      cmd = {
        id: @cmd_id,
        method: cmd_name,
        params: args,
      }
      cmd = JSON.stringify(cmd)
      @sock.send(cmd+@delimiter)
      @cmd_callbacks[@cmd_id] = deferred
      @$log.debug("Send command #{cmd+@delimiter}")

    return deferred.promise

  subscribe: (signal, callback) ->
    if signal not in @signals
      @signals[signal] = []

    if  @signals[signal].length == 0
      @sendCommand("signal.setSubscription", [signal, true])
    @signals[signal].push(callback)

  unsubscribe: (signal) ->
    @signals[signal] = []
    @sendCommand("signal.setSubscription", [signal, false])

DjdWebClient.$inject = ["$q", "$rootScope", "$log"]
angular.module("djdWebui.services", [], ($provide) ->
  $provide.factory("djdclientservice", ($q, $rootScope, $log) ->
    new DjdWebClient($q, $rootScope, $log)
  )
)

# vim: ts=4 sw=4 expandtab
