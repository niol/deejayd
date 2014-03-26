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

    seconds_left = t

    hours = Math.floor(seconds_left / 3600)
    seconds_left = seconds_left % 3600

    minutes = Math.floor(seconds_left / 60)
    seconds_left = seconds_left % 60

    t_formatted = "#{ num(minutes) }:#{ num(seconds_left) }"
    if hours > 0
      t_formatted = "#{ num(hours) }:" + t_formatted
    return t_formatted

angular.module("djdWebui.util", [], ($provide) ->
  $provide.factory("util", () ->
    return new DjdUtil()
  )
)

# vim: ts=4 sw=4 expandtab
