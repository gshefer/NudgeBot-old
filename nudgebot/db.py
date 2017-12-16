
from pymongo import MongoClient

from common import Singleton


class db(object):  # noqa
    __metaclass__ = Singleton

    def __init__(self):
        self.client = MongoClient()
        self.db = self.client.data
        self.records = self.client.db.records
        self.stats = self.client.db.stats

    def add_record(self, cases_checksum, action, action_properties):
        db().records.insert_one({
            'case_checksum': cases_checksum,
            'action': {
                'checksum': action.hash,
                'name': action.name,
                'properties': action_properties
            }
        })

    def add_stat(self, data):
        db().stats.insert_one(data)

    def clear_db(self):
        # Deleting all the data in the db
        self.records.remove()
        self.stats.remove()
