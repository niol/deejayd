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

class DjdApp.Main
  constructor: ->
    # init i18n
    $.i18n.setDictionary(JSON.parse(DjdApp.dictionary))
    # init deejayd client
    deejayd_root_url = DjdApp.options.root_url
    rpc_url = "http://#{location.host}#{deejayd_root_url}rpc/"
    DjdApp.debug(rpc_url)
    @client = new DjdApp.WebClient(rpc_url)

    # create panel menu
    $("#djd-main-panel").panel({
      display: "overlay"
      create: (evt, ui) ->
        $("#djd-main-panel-menu").listview()
    })
    $(document).on("click", ".djd-open-menu", (evt) ->
      $("#djd-main-panel").panel("open")
    )

    # create main footer/header
    $("#djd-header").toolbar()

    @loadingPopup = new DjdApp.LoadingWidgets()
    @loadingPopup.load()

  init: (page_id) ->
    @loadingPopup.close()
    # init controllers
    @player = new DjdApp.PlayerController(@)
    @audiolib = new DjdApp.AudioLibraryController(@)
    @videolib = new DjdApp.VideoLibraryController(@)
    @webradio = new DjdApp.WebradioController(@)

    @loadController(page_id)

  loadController: (page_id) ->
    if page_id == "djd-player-page"
      @player.load()
    else if page_id == "djd-playlist-page"
      @player.loadPlaylist()
    else if page_id == "djd-audiolib-page"
      @audiolib.load()
    else if page_id == "djd-videolib-page"
      @videolib.load()
    else if page_id == "djd-webradio-page"
      @webradio.load()

  setTitle: (title) ->
    $("#djd-title").html(title)

  setHeaderToolbar: (toolbar) ->
    toolbar.appendTo("#djd-header-toolbar")

#  setFooterToolbar: (toolbar) ->
#    @footer.setPageFooter(toolbar)

  close: ->
    @loadingPopup.setError(jQuery.i18n._("connection_lost"))


# disable ajax navigation
$.mobile.ajaxLinksEnabled = false;

init = false
main = null
jQuery(document).on 'pageshow', ->

  page_id = jQuery.mobile.activePage.attr('id')
  if not init
    main = new DjdApp.Main()
    $(document).on("djdClientConnect", (evt) ->
      main.init(page_id)
    )
    $(document).on("djdClientClose", (evt) ->
      main.close()
    )
    init = true
  else
    main.loadController(page_id)

# vim: ts=4 sw=4 expandtab
