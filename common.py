from enum import Enum
from datetime import datetime
from dateutil import tz
import dateparser


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


class Age(object):

    def __init__(self, datetime_obj):
        self._datetime_obj = as_local_time(datetime_obj, raise_if_native_time=False)

    @property
    def total_seconds(self):
        return int((datetime.now() - self._datetime_obj).total_seconds())

    @property
    def days(self):
        return self.total_seconds / 86400

    @property
    def hours(self):
        return (self.total_seconds - self.days * 86400) / 3600

    @property
    def json(self):
        return {'days': self.days, 'hours': self.hours, 'total_seconds': self.total_seconds}

    @property
    def pretty(self):
        return '{} days and {} hours'.format(self.days, self.hours)


def as_local_time(datetime_obj, tzinfo=None, raise_if_native_time=True):
    """Converting the datetime object to local time
    if raise_if_native_time: Raises ValueError: astimezone() cannot be applied to
                             a naive datetime  if provided datetime_obj with tzinfo=None
    """
    if isinstance(datetime_obj, basestring):
        datetime_obj = dateparser.parse(datetime_obj)
    if not datetime_obj.tzinfo and not raise_if_native_time:
        return datetime_obj
    local_dt = datetime_obj.astimezone(tz.tzlocal())
    return local_dt.replace(tzinfo=tzinfo)
