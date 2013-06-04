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
  constructor: (@view) ->
    @title = ""
    @buttons = []

  update: (title, buttons) ->
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
    @refresh()


class DjdApp.widgets.AudioLibraryContextMenu
  constructor: (@view) ->
    @popup = $("#djd-audiolib-popup")
    @menu = $("#djd-audiolib-popup-menu")

  update: (value, type="filter") ->
    @menu.html('')

    self = @
    play_button = $("<a/>", {
      href: "#",
      html: $.i18n._("play")
    }).click((e) ->
      e.preventDefault()
      self.view.controller.play(value, type)
      self.close()
    )
    add_button = $("<a/>", {
      href: "#",
      html: $.i18n._("addPls")
    }).click((e) ->
      e.preventDefault()
      self.view.controller.addToPls(value, type)
      self.close()
    )
    queue_button = $("<a/>", {
      href: "#",
      html: $.i18n._("addQueue")
    }).click((e) ->
      e.preventDefault()
      self.view.controller.addToQueue(value, type)
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
    @toolbar = new DjdApp.widgets.AudioLibraryToolbar(@)
    @menu = new DjdApp.widgets.AudioLibraryContextMenu(@)
    @rating_menu = new DjdApp.widgets.RatingPopup(@controller, "#djd-audiolib-page")
    @loadGenreList()

    # init event handler
    self = @
    for key in ["album", "artist", "genre", "folder", "playlist"]
      btn = $("#djd-audiolib-nav-#{ key }")
      btn.click((e) ->
        if not $(@).hasClass("ui-state-persist")
          $("#djd-audiolib-nav a.ui-state-persist").removeClass("ui-state-persist")
          $(@).addClass("ui-state-persist")

          k = $(@).attr("id").split("-")[3]
          c_key = k.charAt(0).toUpperCase() + k.slice(1)
          self["load#{ c_key }List"]()
      )

  loadPlaylistList: ->

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

          $("#djd-audiolib-footer").hide()
          self.loadAlbumList(a_ft)
        ).on("contextmenu", (e) ->
          e.preventDefault()

          self.menu.update(a_ft)
        )
        $("<li/>").append(anchor).appendTo(self.list)
      )
      self.list.listview( "refresh" );
    )

  loadAlbumList: (filter=null) ->
    self = @
    if filter == null
      @toolbar.reset()
      @setActiveTab("album")
    else
      back_button = $("<a/>", {
        href: "#",
        html: $.i18n._(filter.tag),
      }).click((e) ->
        if filter.tag == 'genre'
          self.loadGenreList()
        else if filter.tag == 'artist'
          self.loadArtistList()
      ).buttonMarkup({
        corners: false,
        icon: "arrow-l",
      })
      @toolbar.update(@format(filter.pattern), [back_button])
    @enableLoading()

    @controller.getAlbum(filter, (a_list) ->
      self.list.html('')
      $(a_list).each((idx, album) ->
        a_ft = new DjdApp.models.MediaBasicFilter("equals", "album_id", album.id)

        anchor = $("<a/>", {
          href: "#",
        }).click((e) ->
          e.preventDefault()

          self.loadSongs(album, filter)
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

  loadSongs: (album, filter) ->
    self = @

    b_title = $.i18n._("albums")
    if filter != null
      b_title = filter.pattern
    back_button = $("<a/>", {
      href: "#",
      html: b_title,
    }).click((e) ->
      self.loadAlbumList(filter)
    ).buttonMarkup({
      corners: false,
      icon: "arrow-l",
    })
    @toolbar.update(@format(album.name), [back_button])
    @enableLoading()

    a_ft = new DjdApp.models.MediaBasicFilter("equals", "album_id", album.id)
    @controller.getSongs(a_ft, (s_list) ->
      self.list.html('')
      $(s_list.getMediaList()).each((idx, song) ->
        s_ft = new DjdApp.models.MediaBasicFilter("equals",
          "id", song.get("media_id")
        )
        anchor = $("<a/>", {
          href: "#",
          html: song.formatMedialist()
        }).click((e) ->
          e.preventDefault()
          self.menu.update(s_ft)
        )
        rating = $("<a/>", {
          href: "#",
        }).click((e) ->
          e.preventDefault()
          self.rating_menu.update(s_ft)
        )
        $("<li/>").append(anchor).append(rating).appendTo(self.list)
      )
      self.list.listview( "refresh" );
    )

  _pathJoin: (paths...) ->
    index = null
    while (index = paths.indexOf("")) != -1
      paths.splice(index, 1);
    if paths.length > 0
      return paths.join("/")
    return ""

  loadFolderList: (folder="") ->
    self = @
    # update toolbar
    if folder == ""
      @toolbar.reset()
    else
      f_list = folder.split("/")
      buttons = []
      rel_path = ""
      a = [""]
      $.each(f_list, (idx, p) ->
        if idx < (f_list.length-1)
          a.push(p)
      )

      for path in a
        title = if path == "" then "/" else path
        rel_path = @_pathJoin(rel_path, path)

        buttons.push($("<a/>", {
          href: "#",
          html: title,
        }).attr("data-djdpath", rel_path).click((e) ->
          e.preventDefault()
          v = $(@).attr("data-djdpath")
          self.loadFolderList(v)
        ).buttonMarkup({
          corners: false,
        }))
      @toolbar.update(f_list[f_list.length-1], buttons)
    @enableLoading()

    # get folder content
    @controller.getFolderContent(folder, (result) ->
      self.list.html('')
      $(result.directories).each((idx, dir) ->
        img = $("<img/>", {
          src: "static/style/djd-images/folder-music.png",
          class: "ui-li-icon",
        })
        anchor = $("<a/>", {
          href: "#",
          text: "#{ dir.name }",
        }).append(img).click((e) ->
          e.preventDefault()
          self.loadFolderList(self._pathJoin(result.root, dir.name))
        ).on("contextmenu", (e) ->
          e.preventDefault()
          self.menu.update([dir.id], "folder")
        )
        $("<li/>").append(anchor).appendTo(self.list)
      )

      $(result.files).each((idx, file) ->
        f_ft = new DjdApp.models.MediaBasicFilter("equals", "id", file.media_id)

        img = $("<img/>", {
          src: "static/style/djd-images/music.png",
          class: "ui-li-icon",
        })
        anchor = $("<a/>", {
          href: "#",
          text: "#{ file.filename }",
        }).append(img).click((e) ->
          e.preventDefault()
          self.menu.update(f_ft)
        ).on("contextmenu", (e) ->
          e.preventDefault()
          self.menu.update(f_ft)
        )
        $("<li/>").append(anchor).appendTo(self.list)
      )
      self.list.listview("refresh")
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
