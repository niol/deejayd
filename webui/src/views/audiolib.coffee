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

class DjdApp.widgets.AudioLibraryToolbar
  constructor: ->
    @title = ""
    @buttons = []
    @history = []

  update: (title, buttons, keep_hist=true) ->
    if keep_hist
      @history.push({
        title: @title,
        buttons: @buttons
      })
    @title = title
    @buttons = buttons

    @refresh()

  refresh: ->
    $("#djd-audiolib-toolbar-title").html(@title)

    $("#djd-audiolib-toolbar-buttons").html('')
    for btn in @buttons
      $("<li/>").append(btn).appendTo("#djd-audiolib-toolbar-buttons")

  reset: ->
    @title = ""
    @buttons = []
    @history = []

    @refresh()


class DjdApp.widgets.AudioLibraryContextMenu
  constructor: (@view) ->
    @popup = $("#djd-audiolib-popup")
    @menu = $("#djd-audiolib-popup-menu")

  update: (filter) ->
    @menu.html('')

    self = @
    play_button = $("<a/>", {
      href: "#",
      html: $.i18n._("play")
    }).click((e) ->
      e.preventDefault()
      self.view.controller.playByFilter(filter)
      self.close()
    )
    add_button = $("<a/>", {
      href: "#",
      html: $.i18n._("addPls")
    }).click((e) ->
      e.preventDefault()
      self.view.controller.addByFilter(filter)
      self.close()
    )
    queue_button = $("<a/>", {
      href: "#",
      html: $.i18n._("addQueue")
    }).click((e) ->
      e.preventDefault()
      self.view.controller.addQueueByFilter(filter)
      self.close()
    )

    for button in [play_button, add_button, queue_button]
      $("<li/>").append(button).appendTo(@menu)
    @menu.listview("refresh")

    @popup.popup("open")

  close: ->
    @popup.popup("close")


class DjdApp.views.AudioLibraryView
  constructor: (@controller) ->
    @list = $("#djd-audiolib-listview")
    @toolbar = new DjdApp.widgets.AudioLibraryToolbar()
    @menu = new DjdApp.widgets.AudioLibraryContextMenu(@)
    @loadGenreList()

    # init event handler
    self = @
    for key in ["album", "artist", "genre", "folder"]
      btn = $("#djd-audiolib-nav-#{ key }")
      btn.click((e) ->
        if not $(@).hasClass("ui-state-persist")
          $("#djd-audiolib-nav a.ui-state-persist").removeClass("ui-state-persist")
          $(@).addClass("ui-state-persist")

          k = $(@).attr("id").split("-")[3]
          c_key = k.charAt(0).toUpperCase() + k.slice(1)
          self["load#{ c_key }List"]()
      )

  loadGenreList: ->
    @toolbar.reset()
    @setActiveTab("genre")
    @enableLoading()

    self = @
    @controller.getGenre((g_list) ->
      self.list.html('')
      $(g_list).each((idx, g) ->
        filter = new DjdApp.models.MediaBasicFilter("equals", "genre", g)

        anchor = $("<a/>", {
          href: "#",
          html: self.format(g)
        }).click((e) ->
          e.preventDefault()
          $("#djd-audiolib-footer").hide()

          back_button = $("<a/>", {
            href: "#",
            html: $.i18n._("genre"),
          }).click((e) ->
            self.loadGenreList()
          )
          back_button.buttonMarkup({
            corners: false,
            icon: "arrow-l",
          })
          self.toolbar.update(self.format(g), [back_button])

          self.loadAlbumList(filter)
        ).on("contextmenu", (e) ->
          e.preventDefault()

          self.menu.update(filter)
        )
        $("<li/>").append(anchor).appendTo(self.list)
      )
      self.list.listview( "refresh" );
    )

  loadArtistList: () ->
    @toolbar.reset()
    @setActiveTab("artist")
    @enableLoading()

    self = @
    @controller.getArtist((a_list) ->
      self.list.html('')
      $(a_list).each((idx, artist) ->
        a_ft = new DjdApp.models.MediaBasicFilter("equals", "artist", artist)

        anchor = $("<a/>", {
          href: "#",
          html: self.format(artist)
        }).click((e) ->
          e.preventDefault()
          self.toolbar.update(self.format(artist), [])
          self.loadAlbumList(a_ft)
        ).on("contextmenu", (e) ->
          e.preventDefault()
          self.menu.update(a_ft)
        )
        $("<li/>").append(anchor).appendTo(self.list)
      )
      self.list.listview( "refresh" );
    )

  loadFolderList: (folder=null) ->

  loadAlbumList: (filter=null) ->
    if filter == null
      @toolbar.reset()
      @setActiveTab("album")
    @enableLoading()

    self = @
    @controller.getAlbum(filter, (a_list) ->
      self.list.html('')
      $(a_list).each((idx, album) ->
        a_ft = new DjdApp.models.MediaBasicFilter("equals", "album_id", album.id)

        anchor = $("<a/>", {
          href: "#",
        }).click((e) ->
          e.preventDefault()
          self.toolbar.update(self.format(album), [])
          self.loadSongs(a_ft)
        ).on("contextmenu", (e) ->
          e.preventDefault()
          self.menu.update(a_ft)
        )
        # add cover image
        img = "static/style/djd-images/missing-cover.png"
        if album.cover_filename != ""
          img = "covers/#{ album.cover_filename }"
        $("<img/>", {
          src: img
        }).appendTo(anchor)
        # add title
        $("<h2/>").html(self.format(album.name)).appendTo(anchor)

        $("<li/>").append(anchor).appendTo(self.list)
      )
      self.list.listview( "refresh" );
    )

  loadSongs: (filter) ->
    @enableLoading()

    self = @
    @controller.getSongs(filter, (s_list) ->
      self.list.html('')
      $(s_list.getMediaList()).each((idx, song) ->
        s_ft = new DjdApp.models.MediaBasicFilter("equals",
          "media_id",
          song.get("media_id")
        )
        anchor = $("<a/>", {
          href: "#",
          html: song.formatMedialist()
        }).click((e) ->
          e.preventDefault()
          self.menu.update(s_ft)
        )
        $("<li/>").append(anchor).appendTo(self.list)
      )
      self.list.listview( "refresh" );
    )

  enableLoading: ->
    @list.html("<li>#{ $.i18n._('loading') }</li>")
    @list.listview( "refresh" );

  setActiveTab: (tab) ->
    $("#djd-audiolib-footer").show()

  format: (str) ->
    if str == ''
      str = "<em>#{ $.i18n._('unknown') }</em>"
    return str
