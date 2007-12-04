import ConfigParser, os, sys, string

class DeejaydConfig:

    custom_conf = None
    __global_conf = '/etc/deejayd.conf'
    __user_conf = '~/.deejayd.conf'
    __config = None

    def __init__(self):

        if DeejaydConfig.__config == None:
            DeejaydConfig.__config = ConfigParser.ConfigParser()

            default_config_path = os.path.abspath(os.path.dirname(__file__))
            DeejaydConfig.__config.readfp(open(default_config_path\
                                        + '/defaults.conf'))

            conf_files = [DeejaydConfig.__global_conf,\
                         os.path.expanduser(DeejaydConfig.__user_conf)]
            if DeejaydConfig.custom_conf:
                conf_files.append(DeejaydConfig.custom_conf)
            DeejaydConfig.__config.read(conf_files)

    def __getattr__(self, name):
        return getattr(DeejaydConfig.__config, name)

    def set(self, section, variable, value):
        self.__config.set(section, variable, value)

    def get_bind_addresses(self, service = 'net'):
        bind_addresses = self.__config.get(service, 'bind_addresses').split(',')
        clean_bind_addresses = map(string.strip, bind_addresses)
        if 'all' in clean_bind_addresses:
            return ['']
        else:
            return map(string.strip, bind_addresses)


# vim: ts=4 sw=4 expandtab
