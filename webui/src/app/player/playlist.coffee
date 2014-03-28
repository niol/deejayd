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

class DjdSourcePlaylistCtrl
  constructor: (@$scope, @util, @localize, @alerts, @djdplayerservice) ->
    self = @
    @pls_infos = {
      audiopls: {id: -1},
      audioqueue: {id: -1},
      videopls: {id: -1},
    }
    @$scope.loading = false
    @$scope.currentPls = "audiopls"
    @$scope.currentId = {pls: "", pos: -1, id: -1}
    @$scope.player = @djdplayerservice

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
          self.djdplayerservice.audioPlsSave(pls_name).then((ans) ->
            self.alerts.info(self.localize._('_playlistSaved_'))
          )
      )
    )

    @$scope.$on('djd:player:pls_updated', (evt, data) ->
      old_id = self.pls_infos[data.pls].id
      self.pls_infos[data.pls] = data.infos
      if self.$scope.currentPls != data.pls
        return

      if old_id < self.pls_infos[data.pls].id
        self.$scope.loadPls(data.pls)
    )

    @$scope.$on("djd:player:current_id_changed", (evt, current_id) ->
      if current_id != ""
        c = current_id.split(":")
        self.$scope.currentId = {
          pls: c[2],
          id: c[1],
          pos: c[0],
        }
        self.$scope.currentPls = self.$scope.currentId.pls
      else
        self.$scope.currentId = {pls: "", pos: -1, id: -1}
    )

    @$scope.$on('$viewContentLoaded', ->
      # subscribe to source playlist events
      self.djdplayerservice.subscribeToSource()
    )
    @$scope.$on('$destroy', ->
      # unsubscribe to source playlist events
      self.djdplayerservice.unsubscribeToSource()
    )

    @$scope.loadPls = (pls) ->
      infos = self.pls_infos[pls]
      type = self.localize._("_songs_")
      if pls == "videopls"
        type = self.localize._("_videos_")
      self.$scope.plsDesc = "#{infos['length']} #{type} (#{self.util.formatTime(infos['timelength']) })"

      funcs = {
        audiopls: "getAudioPlaylist",
        videopls: "getVideoPlaylist",
        audioqueue: "getAudioQueue",
      }

      self.$scope.loading = true
      self.djdplayerservice[funcs[pls]](0, null).then((m_list) ->
        self.$scope.playlist = m_list.getMediaList()
        self.$scope.loading = false
      )
      self.$scope.currentPls = pls

DjdSourcePlaylistCtrl.$inject = ["$scope", "util", "localize", "alerts", "djdplayerservice"]

angular.module('djdWebui.sourcePlaylist', [
  'djdWebui.util',
  'djdWebui.localization',
  'djdWebui.alerts',
  'djdWebui.player.services',
  'ngRoute'
]).config(($routeProvider) ->
  $routeProvider
  .when('/', {
      templateUrl: 'gen/tpl/playlist.tpl.html',
      controller: 'DjdSourcePlaylistCtrl'
    });
).controller('DjdSourcePlaylistCtrl', DjdSourcePlaylistCtrl)

