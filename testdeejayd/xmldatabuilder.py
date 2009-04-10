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


from deejayd.mediafilters import *
from deejayd.net.xmlbuilders import *

from testdeejayd.databuilder import TestData

class DeejaydXMLSampleFactory(DeejaydXMLAnswerFactory):

    def __init__(self):
        super(DeejaydXMLSampleFactory, self).__init__()
        self.sampledata = TestData()

    def get_deejayd_xml_answer(self, ans_type, cmd_name=None):
        if not cmd_name:
            cmd_name = 'cmdName'

        return super(DeejaydXMLSampleFactory,
                     self).get_deejayd_xml_answer(ans_type, cmd_name)

    def getError(self, cmd_name=None):
        error = self.get_deejayd_xml_answer('error', cmd_name)
        error.set_error_text('error text')
        return error

    def getAck(self, cmd_name=None):
        ack = self.get_deejayd_xml_answer('Ack', cmd_name)
        return ack

    def getKeyValue(self, cmd_name=None):
        kv = self.get_deejayd_xml_answer('KeyValue', cmd_name)
        kv.set_pairs(self.sampledata.getSampleParmDict())
        return kv

    def getList(self, cmd_name=None):
        l = self.get_deejayd_xml_answer('List', cmd_name)
        for i in range(2):
            l.contents.append("item%d" % i)
        return l

    def getFileAndDirList(self, cmd_name=None):
        fl = self.get_deejayd_xml_answer('FileAndDirList', cmd_name)
        fl.set_directory('optionnal_described_dirname')
        fl.add_directory('dirName')
        fl.set_filetype('song or video')

        fl.add_file(self.sampledata.getSampleParmDict())

        return fl

    def getMediaList(self, cmd_name=None):
        ml = self.get_deejayd_xml_answer('MediaList', cmd_name)
        ml.set_mediatype("song or video or webradio or playlist")
        ml.add_media(self.sampledata.getSampleParmDict())
        ml.add_media({"parmName1": "parmValue1", \
            "audio": [{"idx": "0", "lang": "lang1"}, \
                      {"idx": "1", "lang": "lang2"}],\
            "subtitle": [{"idx": "0", "lang": "lang1"}]})
        ml.set_filter(self.sampledata.get_sample_filter())
        return ml

    def getDvdInfo(self, cmd_name=None):
        dvd = self.get_deejayd_xml_answer('DvdInfo', cmd_name)
        dvd_info = {'title': "DVD Title", "longest_track": 1,\
                    'track':
                      [ {"ix": 1,\
                         "length":"track length",\
                         "audio":[\
                            { 'ix': 0,\
                              'lang': 'lang code'\
                            }],\
                         "subp":[\
                            { 'ix': 0,\
                              'lang': 'lang code'\
                            },\
                            { 'ix': 1,\
                              'lang': 'lang code'\
                            }],\
                         "chapter":[
                            {'ix': 1,\
                             'length': 'chapter length'\
                            }]\
                        },\
                      ],\
                   }
        dvd.set_info(dvd_info)
        return dvd

    responseTypeExBuilders = {
                               DeejaydXMLError: getError,
                               DeejaydXMLAck: getAck,
                               DeejaydXMLKeyValue: getKeyValue,
                               DeejaydXMLList : getList,
                               DeejaydXMLFileDirList: getFileAndDirList,
                               DeejaydXMLDvdInfo: getDvdInfo,
                               DeejaydXMLMediaList: getMediaList,
                             }

    def get_sample_answer(self, responseClass):
        builder = self.responseTypeExBuilders[responseClass]
        if builder == None:
            return 'No example available.'
        else:
            return builder(self)

    def get_sample_command(self, cmd_name=None):
        if not cmd_name:
            cmd_name = 'status'

        cmd = DeejaydXMLCommand(cmd_name)

        cmd.add_simple_arg('argName1', 'bou')
        cmd.add_simple_arg('argName2', 'bou2')
        cmd.add_multiple_arg('argName3', ['bou2', 'haha', 'aza'])
        cmd.add_simple_arg('argName4', 'bou3')
        cmd.add_multiple_arg('argName5', ['bou2', 'hihi', 'aza'])

        cmd.add_filter_arg('argName6', self.sampledata.get_sample_filter())

        return cmd


# vim: ts=4 sw=4 expandtab
