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


class DjdApp.views.PlaylistToolbar
  constructor: (@view) ->
    @btn_ctrl = $("#djd-playlist-toolbar-buttons").controlgroup("container")
    @order_update = false

    self = @
    clear_btn = $("<a/>", {
      href: "#",
      html: $.i18n._("clear")
    }).click((e) ->
      controller = self.view.controller
      controller.plsClear(self.view.displayed)
    ).buttonMarkup({
      corners: false,
      icon: "delete",
    })
    shuffle_btn = $("<a/>", {
      href: "#",
      html: $.i18n._("shuffle")
    }).click((e) ->
      controller = self.view.controller
      controller.plsShuffle(self.view.displayed)
    ).buttonMarkup({
      corners: false,
      icon: "shuffle",
    })
    buttons = {
      clear: clear_btn,
      shuffle: shuffle_btn
    }
    self.btn_ctrl.append(btn) for k, btn of buttons

    # event handlers
    $("#djd-playlist-toolbar-rpt").change((e) ->
      controller = self.view.controller
      val = $(@).prop( "checked")
      controller.plsOptions(self.view.displayed, "repeat", val)
    )
    $("#djd-playlist-toolbar-order").change((e) ->
      controller = self.view.controller
      val = $(@).val()
      controller.plsOptions(self.view.displayed, "playorder", val)
    )

  update: (pls, infos) ->
    $("#djd-playlist-toolbar-order").html('')
    o_list = ["inorder", "random"]

    if pls != "audioqueue"
      o_list.push("onemedia")
      $("#djd-playlist-toolbar-rpt").checkboxradio("enable")
      $("#djd-playlist-toolbar-rpt").prop( "checked", infos["repeat"])
                                      .checkboxradio( "refresh" );
    else
      $("#djd-playlist-toolbar-rpt").prop( "checked", false)
                                    .checkboxradio( "refresh" );
      $("#djd-playlist-toolbar-rpt").checkboxradio("disable")

    for mode in o_list
      opt = $("<option/>", {
        html: $.i18n._(mode),
        value: mode,
      }).appendTo("#djd-playlist-toolbar-order")
      opt.prop("selected", infos["playorder"] == mode)
    $("#djd-playlist-toolbar-order").selectmenu("refresh")


class DjdApp.views.PlaylistView
  constructor: (@controller) ->
    @playlist = $("#djd-playlist-listview")
    @displayed = "audiopls"
    @pls_infos = {
      audiopls: {id: -1},
      audioqueue: {id: -1},
      videopls: {id: -1},
    }
    @toolbar = new DjdApp.views.PlaylistToolbar(@)

    # define event handlers
    self = @
    for source in ['audiopls', 'audioqueue', 'videopls']
      id = "#djd-playlist-nav-#{ source }"
      $(id).click((e) ->
        s = $(@).attr("data-djd-source")
        self.toolbar.update(s, self.pls_infos[s])
        self.load(s)
      )

  refresh: (pls, infos) ->
    old_id = @pls_infos[pls].id
    @pls_infos[pls] = infos
    if @displayed != pls
      return

    @toolbar.update(pls, infos)
    if old_id < @pls_infos[pls].id
      @load(pls)

  load: (pls) ->
    funcs = {
      audiopls: "getAudioPlaylist",
      videopls: "getVideoPlaylist",
      audioqueue: "getAudioQueue",
    }

    $("#djd-playlist-title").html(@formatTitle(pls, @pls_infos[pls]))
    self = @
    @controller[funcs[pls]](0, null, (m_list) ->
      self.playlist.html('')
      l = m_list.getMediaList()
      $(m_list.getMediaList()).each((idx, m) ->
        item = $("<a/>", {
          href: "#",
          html: m.formatMedialist(),
        }).on("dblclick", (e) ->
          e.preventDefault()
          self.controller.goTo(m.get("id"), pls)
        )

        $("<li/>").append(item).appendTo(self.playlist)
      )
      self.playlist.listview("refresh")
    )
    @displayed = pls

  formatTitle: (pls, infos) ->
    timelength = DjdApp.formatTime(infos["timelength"])
    type = "song"
    if pls == "videopls"
      type = "video"
    type = type+"s" if infos["length"] > 1
    return $.i18n._("plsTitle", [infos["length"], $.i18n._(type), timelength])

# vim: ts=4 sw=4 expandtab
