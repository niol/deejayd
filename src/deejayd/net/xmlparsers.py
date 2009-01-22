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


from deejayd.xmlobject import ET
from deejayd.interfaces import DeejaydSignal
from deejayd.mediafilters import *


class DeejaydXMLParser(object):

    def parse(self, string_io):
        xmlpath = []
        originating_command = ''
        parms = []
        answer = True
        signal = None
        for event, elem in ET.iterparse(string_io,events=("start","end")):
            if event == "start":
                xmlpath.append(elem.tag)
                if len(xmlpath) == 2:
                    if elem.tag in ('error', 'response'):
                        expected_answer = self.get_next_expected_answer()
                    elif elem.tag == 'signal':
                        signal = DeejaydSignal()
                elif elem.tag in ("directory","file","media"):
                    assert xmlpath == ['deejayd', 'response', elem.tag]
                elif elem.tag == "track":
                    assert xmlpath == ['deejayd','response','dvd','track']
                    track = {"audio":[],"subtitle":[],"chapter":[]}
                elif elem.tag in ("audio","subtitle","chapter"):
                    assert xmlpath == ['deejayd','response','dvd','track',\
                                            elem.tag]
                elif elem.tag == "listparm":
                    list_parms = []
                elif elem.tag == "dictparm":
                    dict_parms = {}
                elif elem.tag == 'filter':
                    filter_stack = []
                elif elem.tag == 'sort':
                    sort = []
                elif elem.tag in NAME2COMPLEX.keys():
                    filter_class = NAME2COMPLEX[elem.tag]
                    filter_stack.append(filter_class())
            else: # event = "end"
                xmlpath.pop()

                if elem.tag in ('error','response'):
                    expected_answer.set_originating_command(elem.attrib['name'])
                elif elem.tag == 'signal':
                    signal.set_name(elem.attrib['name'])
                    self.dispatch_signal(signal)
                    signal = None

                if elem.tag == "error":
                    expected_answer.set_error(elem.text)
                elif elem.tag == "response":
                    rsp_type = elem.attrib['type']
                    if rsp_type == "KeyValue":
                        answer = dict(parms)
                    elif rsp_type == "List":
                        answer = [parm[1] for parm in parms]
                    elif rsp_type == "FileAndDirList":
                        if 'directory' in elem.attrib.keys():
                            expected_answer.set_rootdir(elem.\
                                                           attrib['directory'])
                    elif rsp_type == "MediaList":
                        if 'total_length' in elem.attrib.keys():
                            expected_answer.set_total_length(elem.\
                                attrib['total_length'])
                    expected_answer._received(answer)
                    expected_answer = None
                elif elem.tag == "listparm":
                    parms.append((elem.attrib["name"], list_parms))
                elif elem.tag == "listvalue":
                    list_parms.append(elem.attrib["value"])
                elif elem.tag == "dictparm":
                    list_parms.append(dict_parms)
                elif elem.tag == "dictitem":
                    dict_parms[elem.attrib["name"]] = elem.attrib["value"]
                elif elem.tag == "parm":
                    value = elem.attrib["value"]
                    try: value = int(value)
                    except ValueError: pass
                    parms.append((elem.attrib["name"], value))
                elif elem.tag == "media":
                    expected_answer.add_media(dict(parms))
                elif elem.tag == "directory":
                    expected_answer.add_dir(elem.attrib['name'])
                elif elem.tag == "file":
                    expected_answer.add_file(dict(parms))
                elif elem.tag in ("audio","subtitle"):
                    track[elem.tag].append({"ix": elem.attrib['ix'],\
                        "lang": elem.attrib['lang']})
                elif elem.tag == "chapter":
                    track["chapter"].append({"ix": elem.attrib['ix'],\
                        "length": elem.attrib['length']})
                elif elem.tag == "track":
                    track["ix"] = elem.attrib["ix"]
                    track["length"] = elem.attrib["length"]
                    expected_answer.add_track(track)
                elif elem.tag == "dvd":
                    infos = {"title": elem.attrib['title'], \
                             "longest_track": elem.attrib['longest_track']}
                    expected_answer.set_dvd_content(infos)
                elif elem.tag == 'sort':
                    expected_answer.set_sort(sort)
                    del sort
                elif elem.tag == 'sortitem':
                    sort.append((elem.attrib["tag"], elem.attrib["direction"]))
                elif elem.tag == 'filter':
                    expected_answer.set_filter(filter)
                    del filter
                    del filter_stack
                elif elem.tag in NAME2COMPLEX.keys()\
                or elem.tag in NAME2BASIC.keys():
                    if elem.tag in NAME2BASIC.keys():
                        fnd_filter_cls = NAME2BASIC[elem.tag]
                        fnd_filter = fnd_filter_cls(elem.attrib['tag'],
                                                    elem.text)
                    elif elem.tag in NAME2COMPLEX.keys():
                        fnd_filter = filter_stack.pop()
                    try:
                        father_filter = filter_stack[-1]
                    except IndexError:
                        # No father, list is empty
                        filter = fnd_filter
                    else:
                        father_filter.combine(fnd_filter)

                parms = elem.tag in ("parm","listparm","dictparm","listvalue",\
                        "dictitem") and parms or []

                elem.clear()


class DeejaydXMLCommandParser(DeejaydXMLParser):
    # FIXME: Use this instead of the DOM parsing in deejaydProtocol.py
    pass


class DeejaydXMLAnswerParser(DeejaydXMLParser):

    def __init__(self, answer_provider, signal_dispatcher):
        super(DeejaydXMLAnswerParser, self).__init__()
        self.get_next_expected_answer = answer_provider
        self.dispatch_signal = signal_dispatcher


# vim: ts=4 sw=4 expandtab
