import os
import yaml

from common import AttributeDict, Singleton


class conf(object):

    __metaclass__ = Singleton
    CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.yaml')

    def __init__(self, *args, **kwargs):
        self.reload()

    def reload(self):
        if not os.path.exists(self.CONFIG_FILE):
            raise IOError('Config file does not exist, please generate it as '
                          '{} from the template ({}.template)'.format(self.CONFIG_FILE))
        with open(self.CONFIG_FILE, 'r') as confile:
            self._data = AttributeDict.attributize_dict(yaml.load(confile))

    def __getitem__(self, key):
        return self._data[key]

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return self.__getitem__(name)


if __name__ == '__main__':

    # UNITEST

    print conf().github, conf().users
