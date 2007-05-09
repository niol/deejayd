import ConfigParser, os, sys

class DeejaydConfig:

    customConf = None
    __globalConf = '/etc/deejayd.conf'
    __userConf = '~/.deejayd.conf'
    __config = None

    def __init__(self):

        if DeejaydConfig.__config == None:
            DeejaydConfig.__config = ConfigParser.ConfigParser()

            defaultConfigPath = os.path.abspath(os.path.dirname(__file__))
            DeejaydConfig.__config.readfp(open(defaultConfigPath\
                                        + '/defaults.conf'))

            confFiles = [DeejaydConfig.__globalConf,\
                         os.path.expanduser(DeejaydConfig.__userConf)]
            if DeejaydConfig.customConf:
                confFiles.append(DeejaydConfig.customConf)
            DeejaydConfig.__config.read(confFiles)

    def __getattr__(self, name):
        return getattr(DeejaydConfig.__config, name)

    def set(self, section, variable, value):
        self.__config.set(section, variable, value)


# vim: ts=4 sw=4 expandtab
