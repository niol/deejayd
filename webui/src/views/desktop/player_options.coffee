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

class DjdApp.views.PlayerOptionsPopup
  constructor: (@controller) ->
    @modal_popup = $("#djd-modal-popup")
    @current = null
    @is_shown = false

  updateCurrent: (current) ->
    @current = current

  show: () ->
    self = @

    if @current != null
      $(".djd-modal-extra-btn").remove()

      $("#djd-modal-title").html($.i18n._("video_options"))
      $("#djd-modal-body").html("""
  <form class="form-horizontal">
      <div class='form-group'>
          <label class="control-label col-xs-8">#{ $.i18n._('audio_channels') }</label>
          <div class="col-xs-4">
              <select class="form-control" id="djd-video-opts-audiochannels"></select>
          </div>
      </div>

      <div class='form-group' id="djd-video-opts-subchannels-block">
          <label class="control-label col-xs-8">#{ $.i18n._('sub_channels') }</label>
          <div class="col-xs-4">
              <select class="form-control" id="djd-video-opts-subchannels"></select>
          </div>
      </div>

      <div class='form-group' id="djd-video-opts-avoffset-block">
          <label class="control-label col-xs-8">#{ $.i18n._('audio_video_offset') } (ms)</label>
          <div class="col-xs-4">
            <input class="form-control"
                   id="djd-video-opts-avoffset"
                   min="-10000" max="10000" step="100"
                   type="number" placeholder='0'/>
          </div>
      </div>

      <div class='form-group' id="djd-video-opts-suboffset-block">
          <label class="control-label col-xs-8">#{ $.i18n._('sub_offset') } (ms)</label>
          <div class="col-xs-4">
            <input class="form-control"
                   id="djd-video-opts-suboffset"
                   min="-10000" max="10000" step="100"
                   type="number" placeholder='0'/>
          </div>
      </div>
  </form>
      """)

      # a/v offset
      $("#djd-video-opts-avoffset").val(@current.get("av_offset"))
                                    .change((e) ->
        self.controller.setVideoOption("av_offset", $(@).val())
      )

      # audio channels
      for a_channel in @current.get("audio")
        opt = $("<option/>", {
          html: a_channel.lang,
          value: a_channel.ix,
        }).appendTo("#djd-video-opts-audiochannels")
        if @current.get("audio_idx") == a_channel.ix
          opt.attr("selected", "selected")
      $("#djd-video-opts-audiochannels").change((e) ->
        self.controller.setVideoOption("audio_lang", $(@).val())
      )

      # subtitle channels / offset
      if @current.hasAttr("subtitle")
        for s_channel in @current.get("subtitle")
          opt = $("<option/>", {
            html: s_channel.lang,
            value: s_channel.ix,
          }).appendTo("#djd-video-opts-subchannels")
          if @current.get("subtitle_idx") == s_channel.ix
            opt.attr("selected", "selected")
        $("#djd-video-opts-subchannels").change((e) ->
          self.controller.setVideoOption("sub_lang", $(@).val())
        )

        $("#djd-video-opts-suboffset").val(@current.get("sub_offset"))
                                      .change((e) ->
          self.controller.setVideoOption("sub_offset", $(@).val())
        )

        $("#djd-video-opts-subchannels-block").show()
        $("#djd-video-opts-suboffset-block").show()
      else
        $("#djd-video-opts-subchannels-block").hide()
        $("#djd-video-opts-suboffset-block").hide()

      @modal_popup.modal("show")
      @is_shown = true

  hide: () ->
    @modal_popup.modal("hide")
    @is_shown = false

