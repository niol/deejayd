#!/usr/bin/env python
"""
Use to create documentation of the protocol
"""

from deejayd.net import commandsXML,commandsLine
from deejayd.net.xmlbuilders import *

def headerLineCommands():
    return """
                        deejayd - Line Protocol

All data between the client and server is encoded in UTF-8.
-------------------------------------------------------------------------------

Commands Format : 
-----------------  
cmdName arg1 arg2

If arguments contain spaces, they should be surrounded by double quotation
marks, ".

Command Completion :
--------------------
A command returns "OK\\n" on completion or "ACK some error\\n" on failure.
These denote the end of command execution.

Available Commands :
-----------------

------------------
setXML
------------------
description :
Activate XML protocol

------------------
close
------------------
description :
Close connection with deejayd
"""

def headerXMLCommands():
    return """
                        deejayd - XML Protocol

All data between the client and server is encoded in UTF-8.
-------------------------------------------------------------------------------

Activate XML protocol :
-----------------------
By default, line protocole is activated.
To activate XML, you have to send "setXML" command at deejayd 

Commands Format :
-----------------
<?xml version="1.0"?>
<deejayd>
    <command name="cmdName1">
        <arg name="argName1" type="simple">value</arg>
        <arg name="argName2" type="multiple">
            <value>value1</value>
            <value>value2</value>
        </arg>
    </command>
    <command name="cmdName2">
        <arg name="argName1" type="simple">value</arg>
        <arg name="argName2" type="multiple">
            <value>value1</value>
            <value>value2</value>
        </arg>
    </command>
</deejayd>
ENDXML
-----------------
ENDXML is used as command delimeter.
For certain commands, you want to pass several values for an argument. 
Then, you have to set the type to "multiple" instead of "single".


-------------------------------------------------------------------------------
Response Format :
-----------------
<?xml version="1.0"?>
<deejayd>
    <error name="cmdName">errorText</error> // If there is an error.
                 OR
    <response name="cmdName1" type="Ack"/> // No error
    <response name="cmdName2" type="KeyValue">
        <parm name="parmName1" value="value1"/>
        <parm name="parmName2" value="value2"/>
    </response>
    <response name="cmdName3" type="FileList">
        <file>
            <parm name="parmName1" value="parmValue1"
            <parm name="parmName2" value="parmValue2"
        </file>
            OR
        <directory name="dirName"/>
    </response>
    <response name="cmdName3" type="WebradioList">
        <webradio>
            <parm name="parmName1" value="parmValue1"
            <parm name="parmName2" value="parmValue2"
        </webradio>
    </response>
    <response name="cmdName3" type="SongList">
        <song>
            <parm name="parmName1" value="parmValue1"
            <parm name="parmName2" value="parmValue2"
        </song>
    </response>
    <response name="cmdName4" type="PlaylistList">
        <playlist name="pls1"/>
        <playlist name="pls2"/>
    </response>
</deejayd>
-----------------"""

def formatCmdDoc(name,cmdObj, xml = True):
    infos = cmdObj("",[]).docInfos()
    # Args
    argsText = ""
    if "args" in infos:
        for arg in infos["args"]: 
            req = arg["req"] and "true" or "false"
            mult = "false"
            if "mult" in arg: mult = arg["mult"]

            if xml:
                argsText += "%s : type->%s, required->%s, multiple->%s\n" %\
                    (arg["name"],arg["type"],req,mult)
            else:
                argsText += "%s : type->%s, required->%s\n" %\
                    (arg["name"],arg["type"],req)

    return """
-----------------
%(name)s
-----------------
arguments :
%(args)s
description : 
%(descr)s
    """ % {"name":name,
           "args":argsText,
           "descr":infos["description"].strip("\n")
    }


class DeejaydXMLDocFactory(DeejaydXMLAnswerFactory):

    def getSampleParmDict(self, howMuch = 2):
        parmDict = {}
        for i in range(howMuch):
            parmDict['parmName' + str(i)] = 'parmValue' + str(i)
        return parmDict

    def getError(self):
        error = self.getDeejaydXMLAnswer('error', 'cmdName')
        error.setErrorText('error text')
        return error

    def getAck(self):
        ack = self.getDeejaydXMLAnswer('Ack', 'cmdName')
        return ack

    def getKeyValue(self):
        kv = self.getDeejaydXMLAnswer('KeyValue', 'cmdName')
        kv.setParms(self.getSampleParmDict())
        return kv

    def getFileList(self):
        fl = self.getDeejaydXMLAnswer('FileList', 'cmdName')
        fl.addDirectory('dirName')

        fl.addFile(self.getSampleParmDict())

        return fl

    def getWebradioList(self):
        wrl = self.getDeejaydXMLAnswer('WebradioList', 'cmdName')
        wrl.addWebradio(self.getSampleParmDict())
        return wrl

    def getSongList(self):
        sl = self.getDeejaydXMLAnswer('SongList', 'cmdName')
        sl.addSong(self.getSampleParmDict())
        return sl

    def getPlaylistList(self):
        pll = self.getDeejaydXMLAnswer('PlaylistList', 'getPlaylistList')
        pll.addPlaylist('playlist1')
        pll.addPlaylist('playlist2')
        return pll

    responseTypeExBuilders = { DeejaydXMLError: getError,
                               DeejaydXMLAck: getAck,
                               DeejaydXMLKeyValue: getKeyValue,
                               DeejaydXMLFileList: getFileList,
                               DeejaydWebradioList: getWebradioList,
                               DeejaydXMLSongList: getSongList,
                               DeejaydPlaylistList: getPlaylistList }
 
    def getExample(self, responseClass):
        builder = self.responseTypeExBuilders[responseClass]
        if builder == None:
            return 'No example available.'
        else:
            return builder(self)

    def formatResponseDoc(self, response):
        info = {}
        info['type'] = response.responseType
        info['desc'] = response.__doc__
        info['example'] = self.getExample(response).toPrettyXML()

        responseDoc = """
  * %(type)s : %(desc)s
{{{
%(example)s}}}""" % info

        return responseDoc

if __name__ == "__main__":
    # XML Doc
    commandsListXML = commandsXML.commandsList(commandsXML)
    docs = headerXMLCommands()

    docs += """
There are 6 response types :"""

    respDocBuilder = DeejaydXMLDocFactory()
    for response in respDocBuilder.responseTypes:
        docs += respDocBuilder.formatResponseDoc(response)

    docs += """

-------------------------------------------------------------------------------
Available Commands :
-----------------
"""
    for cmd in commandsXML.commandsOrders():
        docs += formatCmdDoc(cmd,commandsListXML[cmd])

    f = open("doc/deejayd_xml_protocol","w")
    try: f.write(docs)
    finally: f.close()

    # Line Doc
    commandsListLine = commandsLine.commandsList(commandsLine)
    docs = headerLineCommands()
    for cmd in commandsLine.commandsOrders():
        try: func = getattr(commandsListLine[cmd]("",[]), "docInfos")
        except AttributeError:
            docs += formatCmdDoc(cmd,commandsListXML[cmd],False)
        else:
            docs += formatCmdDoc(cmd,commandsListLine[cmd],False)

    f = open("doc/deejayd_line_protocol","w")
    try: f.write(docs)
    finally: f.close()


# vim: ts=4 sw=4 expandtab
