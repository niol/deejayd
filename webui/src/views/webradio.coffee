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

class DjdApp.views.WebradioView
  constructor: (@controller) ->
    @top_toolbar = new DjdApp.widgets.WebradioToolbar()

    @active_source = null
    @sources = {}
    @listview = $("#djd-webradio-listview")

  loadSources: (sources) ->
    select = $("#djd-webradio-source-select")
    for source in sources
      @sources[source.name] = source
      $("<option/>", {
        html: $.i18n._(source.name),
        value: source.name,
      }).appendTo(select)

    self = @
    select.selectmenu("refresh").bind("change", (evt) ->
      self.setSource($(@).val())
    )
    @setSource("local")

  setSource: (source_name) ->
    @active_source = source_name
    source = @sources[source_name]
    @controller.getCategories(source_name)

  setCategoriesList: (cats) ->
    self = @

    @top_toolbar.update("#{ cats.length } Categories", [])
    @listview.html("")
    for cat in cats
      link = $("<a/>", {
        html: cat.name,
      }).attr("data-djd-catid", cat.id)
        .attr("data-djd-catname", cat.name).click((evt) ->
          c = {
            id: $(@).attr("data-djd-catid"),
            name: $(@).attr("data-djd-catname"),
          }
          self.controller.getWebradios(self.active_source, c)
        )
      $("<li/>").append(link).appendTo(@listview)
    @listview.listview("refresh")

  setWebradiosList: (cat, webradios) ->
    self = @

    # update toolbars
    back_button = $("<a/>", {
      href: "#",
      html: $.i18n._("allCategories"),
    }).click((e) ->
      self.controller.getCategories(self.active_source)
    ).buttonMarkup({
      corners: false,
      icon: "arrow-l",
    })
    @top_toolbar.update(cat.name, [back_button])

    # update webradio list
    @listview.html("")
    wb_mlist = webradios.getMediaList()
    for wb in wb_mlist
      link = $("<a/>", {
        html: wb.get("title"),
      }).attr("data-djd-wbid", wb.get("wb_id")).click((evt) ->
        w_id = $(@).attr("data-djd-wbid")
        self.controller.playWebradio(w_id)
      )
      $("<li/>").append(link).appendTo(@listview)
    @listview.listview("refresh")


