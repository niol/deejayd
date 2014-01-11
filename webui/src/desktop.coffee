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

class DjdApp.DesktopMain
  constructor: ->
    # init i18n
    $.i18n.setDictionary(JSON.parse(DjdApp.dictionary))
    # init deejayd client
    deejayd_root_url = DjdApp.options.root_url
    rpc_url = "http://#{location.host}#{deejayd_root_url}rpc/"
    DjdApp.debug(rpc_url)
    @client = new DjdApp.WebClient(rpc_url)

  load: ->
    # init global modal popup
    $("#djd-modal-popup").modal({
      show: false,
    })

    @player_controller = new DjdApp.PlayerController(@)
    @player_controller.load()
    @player_controller.loadPlaylist()


jQuery(document).ready( () ->
  main = new DjdApp.DesktopMain()
  $(document).on("djdClientConnect", (evt) ->
    main.load()
  )
  $(document).on("djdClientClose", (evt) ->
  )
)
