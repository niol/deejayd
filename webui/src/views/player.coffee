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

TIMER = 500

class Timer
  constructor: (@action) ->
    @timeout = null

  update: (val) ->
    if @timeout
      clearTimeout(@timeout)
    _ref = @
    @timeout = setTimeout(->
      _ref.action(val)
    , TIMER)


class DjdApp.views.BasePlayerView
  constructor: (@controller) ->
    @volume_uiupdate = false
    player_controller = @controller
    @volume_timer = new Timer((val) ->
      player_controller.setVolume(val)
    )

  load: ->
    # do nothing


class DjdApp.views.DesktopPlayerView extends DjdApp.views.BasePlayerView
  constructor: (@controller) ->
    super(@controller)

    player_controller = @controller
    # init volume slider
    self = @ # ref
    $("#djd-volume-slider").slider()
    $("#djd-volume-slider").on("slide", (e) ->
      if not self.volume_uiupdate
        self.volume_timer.update(jQuery(@).slider("getValue"))
      self.volume_uiupdate = false
    )

    # init player buttons
    $("#djd-player-playtoggle").click((e) ->
      player_controller.playToggle()
    )
    $("#djd-player-stop").click((e) ->
      player_controller.stop()
    )
    $("#djd-player-previous").click((e) ->
      player_controller.previous()
    )
    $("#djd-player-next").click((e) ->
      player_controller.next()
    )

    # init seek buttons
    $("#djd-seek-forward").click((e) ->
      player_controller.seek(10, true)
    )
    $("#djd-seek-fast-forward").click((e) ->
      player_controller.seek(60, true)
    )
    $("#djd-seek-backward").click((e) ->
      player_controller.seek(-10, true)
    )
    $("#djd-seek-fast-backward").click((e) ->
      player_controller.seek(-60, true)
    )

  updateState: (state) ->
    if state == "play"
      $("#djd-player-playtoggle > span").removeClass("glyphicon-play")
                                        .addClass("glyphicon-pause")
    else
      $("#djd-player-playtoggle > span").removeClass("glyphicon-pause")
                                        .addClass("glyphicon-play")

    seek_btns = [
      "#djd-seek-time"
      "#djd-seek-fast-backward"
      "#djd-seek-backward"
      "#djd-seek-forward"
      "#djd-seek-fast-forward"
    ]
    for btn in seek_btns
      if state == "stop"
        $(btn).attr("disabled", "disabled")
      else
        $(btn).removeAttr("disabled")

  updateVolume: (vol) ->
    $("#djd-volume-slider").slider("setValue", vol)

  updateTime: (current, total) ->
    $("#djd-seek-time").html(DjdApp.formatTime(current))

  refreshCurrent: (current) ->
    if current != null
      if current.get("type") != "webradio"
        $("#djd-nowplaying-title").html("""
          <strong>#{ current.get('title') }</strong>
          (#{ DjdApp.formatTime(current.get("length")) })
        """)
      else
        $("#djd-nowplaying-title").html("""
          <strong>#{ current.get('title') }</strong>
        """)
    else
      $("#djd-nowplaying-title").html($.i18n._("no_media"))

  seekDialog: () ->
    $("djd-modal-title").html($.i18n._("seek_dialog_title"))


class DjdApp.views.MobilePlayerView extends DjdApp.views.BasePlayerView
  constructor: (@controller) ->
    super(@controller)

    player_controller = @controller
    # init player buttons
    @buttons = {
      previous: new DjdApp.PlayerButton("previous"),
      play: new DjdApp.PlayerButton("play"),
      stop: new DjdApp.PlayerButton("stop"),
      next: new DjdApp.PlayerButton("next"),
    }
    @buttons.previous.getElt().on("click", (e) ->
      player_controller.previous()
    )
    @buttons.next.getElt().on("click", (e) ->
      player_controller.next()
    )
    @buttons.stop.getElt().on("click", (e) ->
      player_controller.stop()
    )
    @buttons.play.getElt().on("click", (e) ->
      player_controller.playToggle()
    )

    btn_group = new DjdApp.PlayerBouttonGroup()
    for key, btn of @buttons
      btn_group.addButton(btn.getElt())
    btn_group.render("#djd-player-footer")
    @resizeCover()

  # define event handler
    player_view = @ # ref
    jQuery(window).resize(@resizeCover)
    jQuery("#djd-player-slider").change((e) ->
      if not player_view.volume_uiupdate
        player_view.volume_timer.update(jQuery(@).val())
      player_view.volume_uiupdate = false
    )

  resizeCover: ->
    width = jQuery(window).width()
    height = jQuery(window).height()
    height -= jQuery("#djd-player-footer").height()
    height -= jQuery("#djd-player-header").height()

    target = Math.min(width, height) - 60
    jQuery("#djd-player-content").css("background-size", "#{ target }px")
                                 .css("height", "#{ target }px")

  updateVolume: (vol) ->
    @volume_uiupdate = true
    jQuery("#djd-player-slider").val(vol)
    jQuery("#djd-player-slider").slider("refresh")

  updateState: (state) ->
    img = if state == "play" then "pause" else "play"
    @buttons.play.setImage(img)

  updateTime: (current, total) ->
    # do nothing

  refreshCurrent: (current) ->
    if current == null
      @controller.setTitle(jQuery.i18n._("no_media"))
    else
      @controller.setTitle(current.formatTitle())
