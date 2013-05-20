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

class DjdApp.WebClient
  delimiter: 'ENDJSON\n'

  constructor: (@url) ->
    @is_connected = false
    @cmd_id = 0
    @cmd_callbacks = {}
    @signals = {}

    @sock = new SockJS(@url);
    @sock.webClient = @
    @sock.onopen = ->
      DjdApp.debug "Connection to server open"

    @sock.onclose = ->
      DjdApp.debug "Connection to server close"
      @webClient.is_connected = false
      $.event.trigger({
        type: "djdClientClose"
      })

    @sock.onmessage = (e) ->
      msg = e.data
      DjdApp.debug("Receive server message: #{msg}")

      if msg.indexOf("OK DEEJAYD") == 0
        @webClient.is_connected = true
        $.event.trigger({
          type: "djdClientConnect"
        })
      else if msg.indexOf(@webClient.delimiter) > 0
        answer = JSON.parse(msg.substr(0, msg.length-@webClient.delimiter.length))
        if answer.error # some errors happen, display a message
          alert(answer.error)
        else
          if answer.result.type == "signal" # we receive signal dispatch it
            signal = answer.result.answer
            if @webClient.signals.hasOwnProperty(signal.name)
              for cb in @webClient.signals[signal.name]
                cb(signal)
          else if @webClient.cmd_callbacks.hasOwnProperty(answer.id)
            cb = @webClient.cmd_callbacks[answer.id]
            cb(answer.result)

  sendCommand: (cmd_name, args, callback=null) ->
    if @is_connected
      @cmd_id += 1
      cmd = {
        id: @cmd_id,
        method: cmd_name,
        params: args,
      }
      cmd = JSON.stringify(cmd)
      @sock.send(cmd+@delimiter)
      if callback then @cmd_callbacks[@cmd_id] = callback
      DjdApp.debug("Send command #{cmd+@delimiter}")

  subscribe: (signal, callback) ->
    if signal not in @signals
      @signals[signal] = []

    if  @signals[signal].length == 0
      @sendCommand("signal.setSubscription", [signal, true])
    @signals[signal].push(callback)


# vim: ts=4 sw=4 expandtab
