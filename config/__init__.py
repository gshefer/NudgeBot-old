import os
import yaml

from common import AttributeDict, Singleton


class config(object):

    __metaclass__ = Singleton
    DIR = os.path.dirname(__file__)
    CONFIG_FILES = ('config.yaml', 'credentials.yaml')

    def __init__(self, *args, **kwargs):
        self.reload()

    def reload(self):
        self._data = AttributeDict()
        for p in self.CONFIG_FILES:
            conf_name = os.path.splitext(p)[0]
            fp = os.path.join(self.DIR, p)
            if not os.path.exists(fp):
                raise IOError('Config file does not exist, please generate it as '
                              '{} from the template.'.format(fp))
            with open(fp, 'r') as confile:
                self._data[conf_name] = AttributeDict.attributize_dict(yaml.load(confile))

    def __getitem__(self, key):
        return self._data[key]

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return self.__getitem__(name)
