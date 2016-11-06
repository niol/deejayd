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


class DjdPlayerControlsCtrl
  constructor: (@$scope, @djdplayerservice) ->
    self = @
    @volume_timer = new Timer((val) ->
      self.djdplayerservice.setVolume(val)
    )

    @$scope.isPlaying = @djdplayerservice.getState() == "play"
    @$scope.$on("djd:player:state_changed", (evt, state) ->
      self.$scope.isPlaying = state == "play"
    )

    @$scope.volume = @djdplayerservice.getVolume()
    @$scope.$on("djd:player:volume_changed", (evt, volume) ->
      self.$scope.volume = volume
    )

    @$scope.isPlayingVideo = false
    @$scope.$on("djd:player:playing_changed", (evt, track) ->
      self.$scope.isPlayingVideo = false
      if track && track.type == "video"
        self.$scope.isPlayingVideo = true
    )

    @$scope.updateVolume = () ->
      self.volume_timer.update(self.$scope.volume)
    @$scope.player = @djdplayerservice
DjdPlayerControlsCtrl.$inject = ["$scope", "djdplayerservice"]


class DjdPlayerNowPlayingCtrl
  constructor: (@$scope, @localize, @util, @djdplayerservice) ->
    self = @
    @$scope.player = @djdplayerservice
    @$scope.time = "0:00"
    self.setNoMedia()

    @$scope.isSeekable = false
    @$scope.$on("djd:player:playing_changed", (evt, track) ->
      self.$scope.isSeekable = false
      if track
        self.$scope.currentMedia = """
<div class='djd-current-title'>#{track['title']}</div>
<div class='djd-current-desc'>#{self.getDesc(track)}</div>
"""
        if track.type != 'webradio'
          self.$scope.isSeekable = true
      else
        self.setNoMedia()
    )
    @$scope.$on("djd:player:time_changed", (evt, time) ->
      self.$scope.time = self.util.formatTime(time.current)
    )

  getDesc: (track) ->
    if track.type == 'song'
      return "#{track['artist']} - #{track['album']}"
    else if track.type == 'video'
      return "#{track['videowidth']} x #{track['videoheight']}"
    else if track.type == 'webradio'
        return track['webradio-desc']

  setNoMedia: ->
    @$scope.currentMedia = "
<div class='djd-current-nomedia'>#{@localize._('_noMedia_')}</div>
"
DjdPlayerNowPlayingCtrl.$inject = ["$scope", "localize", "util", "djdplayerservice"]


class DjdPlayerSeekDialogCtrl
  constructor: (@$scope, @djdplayerservice) ->
    self = @
    @$scope.hours = 0
    @$scope.minutes = 0
    @$scope.seconds = 0

    @$scope.seek = ->
      if self.$scope.hours != 0 || self.$scope.minutes != 0 || self.$scope.seconds != 0
        self.djdplayerservice.seek(self.$scope.hours*3600 +
                                   self.$scope.minutes*60 +
                                   self.$scope.seconds, false)
        self.$scope.$broadcast("djd:seek-dialog:hide")
    @$scope.$on("djd:seek-dialog:hide", (evt) ->
      $("#djd-modal-seek-dialog").modal("hide")
    )
DjdPlayerSeekDialogCtrl.$inject = ["$scope", "djdplayerservice"]

class DjdPlayerOptionsDialogCtrl
  constructor: (@$scope, @djdplayerservice) ->
    self = @
    @av_offset_timer = new Timer((val) ->
      self.djdplayerservice.setVideoOption("av_offset", val)
    )
    @sub_offset_timer = new Timer((val) ->
      self.djdplayerservice.setVideoOption("sub_offset", val)
    )

    # initial value
    @$scope.audioChannels =[]
    @$scope.subChannels = []
    @$scope.hasSubtitle = false
    @$scope.aspectRatioOptions = ["auto", "1:1", "4:3", "16:9", "16:10", "221:100", "235:100", "239:100", "5:4"]

    @$scope.updateAudioChannel = ->
      self.djdplayerservice.setVideoOption("audio_lang", self.$scope.curAudioChannel)
    @$scope.updateAudioOffset = ->
      self.av_offset_timer.update(self.$scope.audioOffset)
    @$scope.updateSubChannel = ->
      self.djdplayerservice.setVideoOption("sub_lang", self.$scope.subOptions.channel)
    @$scope.updateSubOffset = ->
      self.sub_offset_timer.update(self.$scope.subOptions.offset)
    @$scope.updateAspectRatio = ->
      self.djdplayerservice.setVideoOption("aspect_ratio", self.$scope.aspectRatio)

    # listen playing change event
    @$scope.$on("djd:player:playing_changed", (evt, track) ->
      if track && track['type'] == "video"
        self.$scope.audioChannels = track['audio']
        self.$scope.audioOffset = track['av_offset']
        self.$scope.curAudioChannel = track['audio_idx']

        if track.hasOwnProperty('subtitle')
          self.$scope.subChannels = track['subtitle']
          self.$scope.subOptions = {
            offset  : track['sub_offset'],
            channel : track['subtitle_idx']
          }
          self.$scope.hasSubtitle = true
        else
          self.$scope.hasSubtitle = false

        if track.hasOwnProperty('aspect_ratio')
          self.$scope.aspectRatio = track['aspect_ratio']
        else
          self.$scope.aspectRatio = "auto"
    )
DjdPlayerOptionsDialogCtrl.$inject = ["$scope", "djdplayerservice"]

angular.module("djdWebui.player", [
  'djdWebui.util',
  'djdWebui.localization',
  'djdWebui.player.services',
  'ngSanitize',
]).controller("DjdPlayerControlsCtrl", DjdPlayerControlsCtrl)
  .controller("DjdPlayerNowPlayingCtrl", DjdPlayerNowPlayingCtrl)
  .controller("DjdPlayerSeekDialogCtrl", DjdPlayerSeekDialogCtrl)
  .controller("DjdPlayerOptionsDialogCtrl", DjdPlayerOptionsDialogCtrl)

