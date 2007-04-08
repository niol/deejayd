from xml.dom import minidom


class DeejaydXMLCommand:

    def __init__(self, name):
        self.name = name
        self.args = {}

    def addSimpleArg(self, name, value):
        self.args[name] = value

    def addMultipleArg(self, name, valuelist):
        self.addSimpleArg(name, valuelist)

    def toXML(self):
        xmldoc = minidom.Document()

        # Add root
        xmlroot = xmldoc.createElement('deejayd')
        xmldoc.appendChild(xmlroot)

        # Add command
        xmlcmd = xmldoc.createElement('command')
        xmlcmd.setAttribute('name', self.name)
        xmlroot.appendChild(xmlcmd)

        # Add args
        for arg in self.args.keys():
            xmlarg = xmldoc.createElement('arg')
            xmlarg.setAttribute('name', arg)
            xmlcmd.appendChild(xmlarg)

            argParam = self.args[arg]

            if type(argParam) is list:
                # We've got multiple args
                xmlarg.setAttribute('type', 'multiple')

                for argParamValue in argParam:
                    xmlval = xmldoc.createElement('value')
                    xmlval.appendChild(xmldoc.createTextNode(
                                str(argParamValue) ))
                    xmlarg.appendChild(xmlval)

            else:
                # We've got a simple arg
                xmlarg.setAttribute('type', 'simple')
                xmlarg.appendChild(xmldoc.createTextNode(str(argParam)))

        return xmldoc.toxml('utf-8')


# vim: ts=4 sw=4 expandtab
