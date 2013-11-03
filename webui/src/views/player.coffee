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

class DjdApp.views.PlayerView
  constructor: (@controller) ->
    @volume_uiupdate = false
    player_controller = @controller
    @volume_timer = new Timer((val) ->
      player_controller.setVolume(val)
    )

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

  load: ->
    # do nothing

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

  refreshCurrent: (current) ->
    if current == null
      @controller.setTitle(jQuery.i18n._("no_media"))
    else
      @controller.setTitle(current.formatTitle())
