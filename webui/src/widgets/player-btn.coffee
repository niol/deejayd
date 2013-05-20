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

class DjdApp.PlayerButton
  constructor: (img) ->
    @elt = jQuery("<a/>", {
      href: "#",
      class: "djd-player-btn"
    })
    @setImage(img)

  getElt: ->
    return @elt

  setImage: (img) ->
    img_path = "static/style/djd-images/normal-res/#{ img }.png"
    @elt.css("background-image", "url(#{ img_path })")


class DjdApp.PlayerBouttonGroup
  constructor: ->
    @btn_list = []

  addButton: (btn) ->
    @btn_list.push btn

  render: (parent) ->
    group = jQuery("<div></div>", {
      class: "ui-grid-d",
      id: "djd-player-btn-group",
    }).appendTo(parent)

    btn_ids = ["a", "b", "c", "d", "e"]
    for btn, idx in @btn_list
      jQuery("<div/>", {
        class: "ui-block-#{ btn_ids[idx] }",
        style: "text-align: center;"
      }).append(btn).appendTo(group)


# vim: ts=4 sw=4 expandtab
