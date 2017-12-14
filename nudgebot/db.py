
from pymongo import MongoClient

from common import Singleton


class db(object):  # noqa
    __metaclass__ = Singleton

    def __init__(self):
        self.client = MongoClient()
        self.db = self.client.data
        self.records = self.client.db.records
        self.stats = self.client.db.stats

    def clear_db(self):
        # Deleting all the data in the db
        self.records.remove()
        self.stats.remove()
