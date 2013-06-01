# Deejayd, a media player daemon
# Copyright (C) 2007-2009 Mickael Royer <mickael.royer@gmail.com>
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


class DjdApp.widgets.RatingPopup
  constructor: (@controller, page) ->
    @filter = -1
    # buil popup
    @popup = $("<div/>").appendTo(page)
    list = $("<ul/>").appendTo(@popup)

    self = @
    for i in [0..4]
      a = $("<a/>", {
        "data-djd-rating": i
      }).click((e) ->
        v = $(@).attr("data-djd-rating")
        self.controller.setRating(self.filter, v)
        self.popup.popup("close")
      )
      for j in [0..3]
        cls = if j<i then "djd-icon-star" else "djd-icon-star-off"
        $("<span/>", {
          class: cls,
        }).appendTo(a)
      $("<li/>").append(a).appendTo(list)
    list.listview()
    @popup.popup()

  update: (s_ft) ->
    @filter = s_ft
    @popup.popup("open")

# vim: ts=4 sw=4 expandtab
