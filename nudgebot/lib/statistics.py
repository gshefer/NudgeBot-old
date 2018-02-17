from common import AttributeDict


class stat_property(object):
    def __init__(self, getter):
        self.__doc__ = getattr(getter, '__doc__')
        self.getter = getter

    def uncache(self):
        if self.getter.__name__ in self.obj:
            del self.obj[self.getter.__name__]

    def __get__(self, obj, cls):
        self.obj = obj
        return self

    def __call__(self):
        if self.getter.__name__ in self.obj:
            return self.obj[self.getter.__name__]
        value = self.obj[self.getter.__name__] = self.getter(self.obj)
        return value


class Statistics(AttributeDict):

    def uncache_all(self):
        for k in self.keys():
            # PLease do not iterate over self since it causes:
            # RuntimeError: dictionary changed size during iteration
            del self[k]
