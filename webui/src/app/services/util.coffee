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

class DjdUtil

  formatTime: (t) ->
    num = (n) ->
      if n < 10
        return "0#{ n }"
      else
        return "#{ n }"

    d = new Date(t*1000)
    if t < 3600
      return "#{ num(d.getMinutes()) }:#{ num(d.getSeconds()) }"
    else
      return "#{ num(d.getHours()) }:#{ num(d.getMinutes()) }:#{ num(d.getSeconds()) }"

angular.module("djdWebui.util", [], ($provide) ->
  $provide.factory("util", () ->
    return new DjdUtil()
  )
)

# vim: ts=4 sw=4 expandtab
