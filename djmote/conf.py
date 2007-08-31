import os

class Config:

    def __init__(self, file):
        self.file = os.path.normpath(file)
        self.contents = {}
        if not os.path.isfile(self.file):
            self.__initialize()
        else:
            self.load()

    def __initialize(self):
        self.contents['host'] = 'media'
        self.contents['port'] = 6800
        self.contents['connect_on_startup'] = False
        self.save()

    def save(self):
        f = open(self.file, 'w')
        for item in self.contents.items():
            str_item = map(lambda x: str(x), item)
            f.write('='.join(str_item) + '\n')
        f.close()

    def load(self):
        f = open(self.file, 'r')
        for line in f.readlines():
            (key, val) = line.rstrip('\n').split('=')
            if val == 'True':
                self.contents[key] = True
            elif val == 'False':
                self.contents[key] = False
            else:
                try:
                    self.contents[key] = int(val)
                except ValueError:
                    self.contents[key] = val
        f.close()

    def __getattr__(self, name):
        return getattr(self.contents, name)


# vim: ts=4 sw=4 expandtab
