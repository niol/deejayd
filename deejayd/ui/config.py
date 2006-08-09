import ConfigParser, os, sys

class DeejaydConfig:

    __config = None

    def __init__(self):

        if DeejaydConfig.__config == None:
            DeejaydConfig.__config = ConfigParser.ConfigParser()

            defaultConfigPath = os.path.abspath(os.path.dirname(__file__))
            DeejaydConfig.__config.readfp(open(defaultConfigPath
                                        + '/defaults.conf'))

            DeejaydConfig.__config.read(['/etc/deejayd.conf',
                                    os.path.expanduser('~/.deejayd.conf')])

    def __getattr__(self, name):
        return getattr(DeejaydConfig.__config, name)


# vim: ts=4 sw=4 expandtab
