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


class DjdWebradioService
  constructor: (@djdclientservice, @$rootScope) ->
    self = @

  connect: ->
    self = @
    @subscribe = () ->
      self.djdclientservice.subscribe("webradio.listupdate", (sig) ->
        self.$rootScope.$broadcast("djd:webradio:listUpdated", sig.attrs.source)
      )
      self.djdclientservice.sendCommand("webradio.getAvailableSources", []).then((sources) ->
        self.$rootScope.$broadcast("djd:webradio:sourceListUpdated", sources)
      )
    if @djdclientservice.is_connected
      @subscribe()
    else
      @$rootScope.$on("djd:client:connected", (evt, data) ->
        self.subscribe()
      )

  disconnect: ->
    if @djdclientservice.is_connected
      @djdclientservice.unsubscribe("webradio.listupdate")

  playWebradio: (wbId) ->
    @djdclientservice.sendCommand("webradio.playWebradio", [wbId])

  getCategories: (source_name) ->
    @djdclientservice.sendCommand("webradio.getSourceCategories", [source_name])

  addCategory: (source_name, catName) ->
    @djdclientservice.sendCommand("webradio.sourceAddCategory", [source_name, catName])

  eraseCategory: (source_name, catId) ->
    @djdclientservice.sendCommand("webradio.sourceDeleteCategories", [source_name, [catId]])

  getWebradios: (source_name, cat=null) ->
    args = [source_name]
    if cat != null then args.push(cat.id)
    @djdclientservice.sendCommand("webradio.getSourceContent", args)

  addWebradio: (source_name, catId, wName, wUrl) ->
    @djdclientservice.sendCommand("webradio.sourceAddWebradio", [source_name, wName, [wUrl], catId])

  eraseWebradio: (source_name, w_id) ->
    @djdclientservice.sendCommand("webradio.sourceDeleteWebradios", [source_name, [w_id]])

  clearWebradios: (source_name) ->
    @djdclientservice.sendCommand("webradio.sourceClearWebradios", [source_name])

DjdWebradioService.$inject = ["djdclientservice", "$rootScope"]

angular.module("djdWebui.webradio.services", [
  "djdWebui.services"
], ($provide) ->
  $provide.factory("djdwebradioservice", (djdclientservice, $rootScope) ->
    return new DjdWebradioService(djdclientservice, $rootScope)
  )
)
