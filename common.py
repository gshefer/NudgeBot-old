from enum import Enum


class ExtendedEnum(Enum):
    @classmethod
    def values(cls):
        return [field.value for field in cls]

    @classmethod
    def get_by_value(cls, value):
        for field in cls:
            if field.value == value:
                return field
        raise ValueError('Could not find value "{}" in enum[{}]'.format(value, cls.values()))


class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

    @classmethod
    def attributize_dict(cls, obj):
        if isinstance(obj, dict):
            attr_dict = cls()
            for key, value in obj.items():
                attr_dict[key] = cls.attributize_dict(value)
            return attr_dict
        elif isinstance(obj, (list, tuple)):
            nested_list = list()
            for value in obj:
                nested_list.append(cls.attributize_dict(value))
            return nested_list
        return obj


class Singleton(type):

    _instances = {}

    def __call__(self, *args, **kwargs):
        if self not in self._instances:
            self._instances[self] = super(Singleton, self).__call__(*args, **kwargs)
        return self._instances[self]
