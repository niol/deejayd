# Deejayd, a media player daemon
# Copyright (C) 2007-2017 Mickael Royer <mickael.royer@gmail.com>
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

try:
    import builtins
except ImportError:
    import __builtin__ as builtins
import gettext


class DeejaydTranslations(gettext.GNUTranslations):

    def __init__(self, *args, **kwargs):
        self._catalog = {}
        self.plural = lambda n: n > 1
        gettext.GNUTranslations.__init__(self, *args, **kwargs)

    def install(self, is_unicode=True):
        if is_unicode:
            builtins.__dict__["_"] = self.ugettext
            builtins.__dict__["ngettext"] = self.ungettext
        else:
            builtins.__dict__["_"] = self.gettext
            builtins.__dict__["ngettext"] = self.ngettext
