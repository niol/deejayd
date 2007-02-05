#!/usr/bin/env python
"""
Use to create documentation of the protocol
"""

from deejayd.net import commandsXML

def headerLineCommands():
    pass

def headerXMLCommands():
    return """
                        deejayd - XML Protocol

All data between the client and server is encoded in UTF-8.
-------------------------------------------------------------------------------
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
-----------------
There are 6 response types
  * "Ack" : just an acknowledgement of the command 
  * "KeyValue" : a list of "key=value" couple  
  * "FileList" : file and directory list
  * "WebradioList" : webradio list with informations foreach webradio 
                     (id,pos,title,url)
  * "SongList" : song list (playlist content for example) with informations
                 foreach song (artist,album,title,id...) 
  * "PlaylistList" : playlist list 

-------------------------------------------------------------------------------
Available Commands :
-----------------

    """

def formatCmdDoc(name,cmdObj):
    infos = cmdObj("",[]).docInfos()
    # Args
    argsText = ""
    if "args" in infos:
        for arg in infos["args"]: 
            req = arg["req"] and "true" or "false"
            mult = "false"
            if "mult" in infos: mult = arg["mult"]

            argsText += "%s : type->%s, required->%s, multiple->%s\n" %\
                (arg["name"],arg["type"],req,mult)

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


if __name__ == "__main__":
    commandsList = commandsXML.commandsList(commandsXML)
    docs = headerXMLCommands()
    for cmd in commandsXML.commandsOrders():
        docs += formatCmdDoc(cmd,commandsList[cmd])

    f = open("doc/deejayd_xml_protocol","w")
    try: f.write(docs)
    finally: f.close()

# vim: ts=4 sw=4 expandtab
