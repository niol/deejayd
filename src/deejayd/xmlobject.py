# Deejayd, a media player daemon
# Copyright (C) 2007-2008 Mickael Royer <mickael.royer@gmail.com>
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

try: from xml.etree import cElementTree as ET # python 2.5
except ImportError: # python 2.4
    import cElementTree as ET


class DeejaydXMLObject(object):

    def _to_xml_string(self, s):
        if isinstance(s, int) or isinstance(s, float) or isinstance(s, long):
            return "%d" % (s,)
        elif isinstance(s, str):
            return "%s" % (s.decode('utf-8'))
        elif isinstance(s, unicode):
            rs = s.encode("utf-8")
            return "%s" % (rs.decode('utf-8'))
        else:
            raise TypeError

    def _indent(self,elem, level=0):
        indent_char = "    "
        i = "\n" + level*indent_char
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + indent_char
            for e in elem:
                self._indent(e, level+1)
                if not e.tail or not e.tail.strip():
                    e.tail = i + indent_char
            if not e.tail or not e.tail.strip():
                e.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def to_xml(self):
        return '<?xml version="1.0" encoding="utf-8"?>' + \
            ET.tostring(self.xmlroot,'utf-8')

    def to_pretty_xml(self):
        self._indent(self.xmlroot)
        return '<?xml version="1.0" encoding="utf-8"?>' + "\n" +\
            ET.tostring(self.xmlroot,'utf-8') + "\n"


# vim: ts=4 sw=4 expandtab
