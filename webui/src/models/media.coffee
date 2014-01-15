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

class DjdApp.models.Media
  constructor: (@media) ->

  formatTitle: ->
    return @media.title

  formatMedialist: ->
    rating = $("<div/>")
    for i in [1..@media.rating]
      $("<span/>", {
        class: "djd-icon-star",
      }).appendTo(rating)

    return """
           <p class="ui-li-aside">#{ @formatLength() }</p>
           <h4>#{ @media.title }</h4>
           <p class="djd-li-rating">#{ rating.html() }</p>
           <p class="djd-li-desc"><em>#{ @media.artist } - #{ @media.album }</em></p>
           """

  getMedia: ->
    return @media

  get: (attr) ->
    return @media[attr]

  hasAttr: (attr) ->
    for k, v of @media
      if k is attr then return true
    return false

  formatLength: ->
    return DjdApp.formatTime(@media["length"])

# vim: ts=4 sw=4 expandtab
