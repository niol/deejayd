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

class DjdApp.LoadingWidgets

  load: ->
    content = @renderLoading()
    @elt = jQuery("<div/>", {
      "id": "djd-loading-widget",
      html: content,
    }).appendTo($(document.body))

  close: ->
    @elt.hide()

  setError: (err) ->
    @elt.html(@renderError(err)).show()

  renderLoading: ->
    img_tpl = """
             <div id="djd-loading-img"></div>
             <div id="djd-loading-text">Loading...</div>
             """
    return img_tpl

  renderError: (err) ->
    return """
           <div id="djd-loading-error" class="ui-corner-all">
               <span>#{ err }</span>
           </div>
           """

# vim: ts=4 sw=4 expandtab
