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


class DjdApp.views.DesktopPlaylistView
  constructor: (@controller) ->
    @displayed = "audiopls"
    @pls_infos = {
      audiopls: {id: -1},
      audioqueue: {id: -1},
      videopls: {id: -1},
    }
    @load()

  load: () ->
    self = @
    $("#djd-main-sidebar").html(@sidebar_tpl())
    @menu_entries = {
      audiopls: $("#djd-audiopls-menu"),
      audioqueue: $("#djd-audioqueue-menu"),
      videopls: $("#djd-videopls-menu"),
    }
    $('#djd-pls-menu-container').affix({
      offset: {
        top: 0,
      , bottom: 200,
      }
    })
    # init events handler for sidebar
    for pls, menu of @menu_entries
      menu.children(":first").click((e) ->
        pls_name = $(@).attr("data-djdpls")
        if self.displayed != pls_name
          self.loadPls(pls_name)
          self.active_menu(pls_name)
      )

    $("#djd-main-toolbar").html(@toolbar_tpl())
    # init events handler for toolbar
    $("#djd-pls-shuffle").click((e) ->
      self.controller.plsShuffle(self.displayed)
    )
    $("#djd-pls-clear").click((e) ->
      self.controller.plsClear(self.displayed)
    )

    $("#djd-pls-save").popover({
      html: true,
      placement: "bottom",
      content: """
<input id="djd-pls-savename" class="form-control" placeholder="Enter playlist name" type="text"/>
<button type="submit" id="djd-pls-savebtn" class="pull-right btn btn-default">Save</button>
"""
    }).click((e) ->
      $("#djd-pls-savebtn").click((e) ->
        pls_name = $("#djd-pls-savename").val()
        if pls_name != ""
          self.controller.audioPlsSave(pls_name, (ans) ->
            new DjdApp.views.DesktopAlerts("The playlist has been saved")
          )
      )
    )

    $("#djd-main-content").html(@content_tpl())
    @playlist = $("#djd-pls-listgroup")

  unload: () ->

  refresh: (pls, infos) ->
    old_id = @pls_infos[pls].id
    @pls_infos[pls] = infos
    if @displayed != pls
      return

    if old_id < @pls_infos[pls].id
      @loadPls(pls)

  loadPls: (pls) ->
    infos = @pls_infos[pls]
    type = $.i18n._("songs")
    if pls == "videopls"
      type = $.i18n._('videos')
    $("#djd-pls-desc").html("#{infos['length']} #{type} (#{DjdApp.formatTime(infos['timelength']) })")

    funcs = {
      audiopls: "getAudioPlaylist",
      videopls: "getVideoPlaylist",
      audioqueue: "getAudioQueue",
    }

    self = @
    @controller[funcs[pls]](0, null, (m_list) ->
      self.playlist.html('')
      l = m_list.getMediaList()
      $(m_list.getMediaList()).each((idx, m) ->
        item = $("<a/>", {
          href: "#",
          class: "list-group-item djd-medialist-item",
          html: self.formatMediaEntry(m),
        }).on("click", (e) ->
          e.preventDefault()
        )

        item.appendTo(self.playlist)
      )

      # init event handlers for playlist
      $(".djd-pls-play").click((e) ->
        id = $(@).attr("data-djdid")
        self.controller.goTo(id, self.displayed)
      )
      $(".djd-pls-remove").click((e) ->
        id = $(@).attr("data-djdid")
        self.controller.plsRemove(self.displayed, [id])
      )
    )

    # hide save button if not audiopls
    if pls == "audiopls"
      $("#djd-pls-save").show()
    else
      $("#djd-pls-save").hide()
    @displayed = pls

  formatMediaEntry: (media) ->
    return """
<div class="dropdown pull-right">
  <button class="btn btn-default dropdown-toggle" id="dropdownMenu1" data-toggle="dropdown">
      <span class="glyphicon glyphicon-align-justify"></span>
  </button>
  <ul class="dropdown-menu" role="menu" aria-labelledby="dropdownMenu1">
    <li role="presentation"><a class="djd-pls-play" data-djdid="#{ media.get('id') }" role="menuitem" tabindex="-1" href="#">Play</a></li>
    <li role="presentation" class="divider"></li>
    <li role="presentation"><a class="djd-pls-remove" data-djdid="#{ media.get('id') }" role="menuitem" tabindex="-1" href="#">Remove</a></li>
  </ul>
</div>
<h4>#{ media.formatTitle() } (#{ media.formatLength() })</h4>
<p>#{ media.get("artist") } - #{ media.get("album") }</p>
"""

  content_tpl: () ->
    return """
<div id="djd-pls-listgroup" class="list-group djd-medialist"/>
"""

  sidebar_tpl: () ->
    return  """
<div id="djd-pls-menu-container">
  <ul class="nav nav-pills nav-stacked" id="djd-pls-menu">
      <li id="djd-audiopls-menu" class="active">
          <a data-djdpls="audiopls" href="#">Audio Playlist</a>
      </li>
      <li id="djd-audioqueue-menu" class="">
          <a data-djdpls="audioqueue" href="#">Audio Queue</a>
      </li>
      <li id="djd-videopls-menu" class="">
          <a data-djdpls="videopls" href="#">Video Playlist</a>
      </li>
  </ul>
</div>
"""

  toolbar_tpl: () ->
    return  """
<p class="navbar-text" id="djd-pls-desc"></p>
<div class="navbar-right">
  <button id="djd-pls-shuffle" type="button" class="btn btn-default navbar-btn">
      <span class="glyphicon glyphicon-random"></span>
  </button>
  <button id="djd-pls-save" type="button" class="btn btn-default navbar-btn">
      <span class="glyphicon glyphicon-save"></span>
  </button>
  <button id="djd-pls-clear" type="button" class="btn btn-default navbar-btn">
      <span class="glyphicon glyphicon-trash"></span>
  </button>
</div>
"""

  active_menu: (pls) ->
    for pls_name, menu of @menu_entries
      if pls == pls_name
        menu.addClass("active")
      else
        menu.removeClass("active")

