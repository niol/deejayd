
import os,shutil
from twisted.web import static,server
from twisted.web.resource import Resource

from deejayd.interfaces import DeejaydError
from deejayd.webui.xmlanswer import DeejaydWebAnswer,build_web_interface
from deejayd.webui import commands

class DeejaydWebError(Exception): pass
default_path = os.path.abspath(os.path.dirname(__file__))

class DeejaydMainHandler(Resource):

    def __init__(self, config):
        Resource.__init__(self)
        self.lang = config.get("webui","lang")

    def getChild(self, name, request):
        if name == '': return self
        return Resource.getChild(self,name,request)

    def render_GET(self, request):
        request.setHeader("Content-Type", "application/vnd.mozilla.xul+xml")
        try: rs = build_web_interface(self.lang)
        except IOError, err:
            raise DeejaydWebError(err)
        return rs


class DeejaydCommandHandler(Resource):
    isLeaf = True

    def __init__(self, deejayd, rdf_dir):
        Resource.__init__(self)
        self.__deejayd = deejayd
        self.__rdf_dir = rdf_dir

    def render_GET(self,request):
        return self.__render(request,"get")

    def render_POST(self,request):
        return self.__render(request,"post")

    def __render(self, request, type):
        # init xml answer
        request.setHeader("Content-type","text/xml")
        ans = DeejaydWebAnswer(self.__rdf_dir)

        try: action = request.args["action"]
        except KeyError:
            ans.set_error("you have to enter an action")
            return ans.to_xml()
        try: cmd_cls = commands.commands[action[0]]
        except KeyError:
            ans.set_error("Command %s not found" % action[0])
            return ans.to_xml()

        if cmd_cls.method != type:
            ans.set_error("command send with invalid method")
        else:
            cmd = cmd_cls(self.__deejayd,ans)
            try:
                cmd.argument_validation(request.args)
                cmd.execute()
                cmd.default_result()
            except DeejaydError, err:
                ans.set_error("%s" % err)
            except commands.ArgError, err:
                ans.set_error("bad argument : %s" % err)

        return ans.to_xml()


def init(deejayd_core, config, webui_logfile):
    # create tmp directory
    rdf_dir = config.get("webui","rdf_dir")
    if os.path.isdir(rdf_dir):
        try: shutil.rmtree(rdf_dir)
        except IOError:
            raise DeejaydWebError("Unable to remove rdf directory %s"%rdf_dir)
    try: os.mkdir(rdf_dir)
    except IOError:
        raise DeejaydWebError("Unable to create rdf directory %s" % rdf_dir)

    root = DeejaydMainHandler(config)
    root.putChild("commands",DeejaydCommandHandler(deejayd_core, rdf_dir))

    htdocs_dir = config.get("webui","htdocs_dir")
    if not os.path.isdir(htdocs_dir):
        raise DeejaydWebError("Htdocs directory %s does not exists"%htdocs_dir)
    root.putChild("static",static.File(htdocs_dir))
    root.putChild("rdf",static.File(rdf_dir))

    return server.Site(root, logPath=webui_logfile)

# vim: ts=4 sw=4 expandtab
