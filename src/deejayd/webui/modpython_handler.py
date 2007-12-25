
import os
from mod_python import apache,util
from deejayd.net.client import DeejayDaemonSync, ConnectError
from deejayd.webui import commands, xmlanswer
from deejayd.interfaces import DeejaydError

class InitError(Exception): pass
class NotFoundError(Exception): pass

class Gateway:

    def __init__(self, request):
        self.__req = request
        self.__validate_options()

    def __validate_options(self):
        self.__opt = {}
        opt = self.__req.get_options()

        if "DeejaydUriRoot" not in opt:
            raise InitError("You have to define DeejaydUriRoot option")
        self.__opt["root_uri"] = opt["DeejaydUriRoot"].rstrip("/")
        self.__opt["host"] = "DeejaydHost" in opt.keys() and opt["DeejaydHost"]\
                                                          or "localhost"
        self.__opt["port"] = "DeejaydPort" in opt.keys() and \
                                int(opt["DeejaydPort"]) or 6800

        self.__opt["rdf_dir"] = "DeejaydRDFDir" in opt.keys() and \
                opt["DeejaydRDFDir"] or "/tmp/deejayd_webui_modpython"
        if not os.path.isdir(self.__opt["rdf_dir"]):
            try: os.mkdir(self.__opt["rdf_dir"])
            except IOError:
                raise InitError("Unable to create rdf directory %s"\
                                    % self.__opt["rdf_dir"])

    def run(self):
        path = self.__req.uri.rstrip("/")
        if not path.startswith(self.__opt["root_uri"]):
            raise NotFoundError

        path = path.lstrip(self.__opt["root_uri"])
        if path == '': # init
            self.__req.content_type = "application/vnd.mozilla.xul+xml"
            self.__req.write(xmlanswer.build_web_interface("en"))

        elif path == 'commands':
            args = util.FieldStorage(self.__req)
            ans = xmlanswer.DeejaydWebAnswer(self.__opt["rdf_dir"])
            self.__req.content_type = "text/xml"

            deejayd = DeejayDaemonSync()
            try: deejayd.connect(self.__opt["host"], self.__opt["port"])
            except ConnectError, e:
                ans.set_error(str(e))
                self.__req.write(ans.to_xml())
                return

            try: action = args["action"]
            except KeyError:
                ans.set_error("you have to enter an action")
            else:
                try: cmd_cls = commands.commands[action]
                except KeyError:
                    ans.set_error("Command not found")
                else:
                    if cmd_cls.method != self.__req.method.lower():
                        ans.set_error("command send with invalid method")
                    else:
                        cmd = cmd_cls(deejayd,ans)
                        try:
                            cmd.argument_validation(args)
                            cmd.execute()
                            cmd.default_result()
                        except DeejaydError, err:
                            ans.set_error(str(err))
                        except commands.ArgError, err:
                            ans.set_error("bad argument : %s" % str(err))

            self.__req.write(ans.to_xml())
            deejayd.disconnect()

        else: raise NotFoundError


def handler(request):
    try: obj = Gateway(request)
    except InitError, err:
        request.write("Error : %s" % err)
    else:
        try: obj.run()
        except NotFoundError:
            return apache.HTTP_NOT_FOUND

    return apache.OK

# vim: ts=4 sw=4 expandtab
