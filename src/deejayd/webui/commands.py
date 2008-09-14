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

class ArgError(Exception): pass

class _Command(object):
    method = "get"
    command_args = []

    def __init__(self, deejayd, answer):
        self._deejayd = deejayd
        self._answer = answer
        self._args = {}

    def argument_validation(self, http_args):
        for arg in self.command_args:
            if arg['name'] in http_args:
                # format http parms
                value = http_args[arg['name']]
                if "mult" in arg.keys() and arg["mult"]:
                    if not isinstance(value, list): value = [value]
                    self._args[arg['name']] = value
                else:
                    if isinstance(value, list): value = value[0]
                    self._args[arg['name']] = value
                    value = [value]

                for v in value:
                    if arg['type'] == "string":
                        try: v.split()
                        except AttributeError:
                            raise ArgError(_("Arg %s (%s) is not a string") % \
                                (arg['name'], str(v)))

                    elif arg['type'] == "int":
                        try: v = int(v)
                        except (ValueError,TypeError):
                            raise ArgError(_("Arg %s (%s) is not a int") %\
                                (arg['name'], str(v)))

                    elif arg['type'] == "enum_str":
                        if v not in arg['values']:
                            raise ArgError(\
                                _("Arg %s (%s) is not in the possible list")\
                                % (arg['name'],str(v)))

                    elif arg['type'] == "enum_int":
                        try: v = int(v)
                        except (ValueError,TypeError):
                            raise ArgError(_("Arg %s (%s) is not a int") %\
                                (arg['name'], str(v)))
                        else:
                            if v not in arg['values']:
                                raise ArgError(\
                                    _(\
                                    "Arg %s (%s) is not in the possible list")\
                                    % (arg['name'],str(v)))

                    elif arg['type'] == "regexp":
                        import re
                        if not re.compile(arg['value']).search(v):
                            raise ArgError(\
                            _("Arg %s (%s) not match to the regular exp (%s)") %
                                (arg['name'],str(v),arg['value']))

            elif arg['req']:
                raise ArgError(_("Arg %s is mising") % arg['name'])
            else:
                self._args[arg['name']] = arg['default']

    def default_result(self):
        raise NotImplementedError

    def execute(self):
        raise NotImplementedError

# vim: ts=4 sw=4 expandtab
