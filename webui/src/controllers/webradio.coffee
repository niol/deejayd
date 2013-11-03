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

class DjdApp.WebradioController
  constructor: (@main_controller) ->
    # init var
    @sources = {}
    @is_loaded = false
    @rpc_client = @main_controller.client

  load: ->
    if not @is_loaded
      self = @

      @view = new DjdApp.views.WebradioView(@)
      @rpc_client.sendCommand("webradio.getAvailableSources", [], (result) ->
        self.view.loadSources(result)
      )
      # load is finish
      @is_loaded = true

  getCategories: (source_name) ->
    @rpc_client.sendCommand("webradio.getSourceCategories", [source_name], (result) =>
      @view.setCategoriesList(result)
    )

  getWebradios: (source_name, cat=null) ->
    args = [source_name]
    if cat != null then args.push(cat.id)
    @rpc_client.sendCommand("webradio.getSourceContent", args, (result) =>
      @view.setWebradiosList(cat, result)
    )

  playWebradio: (w_id) ->
