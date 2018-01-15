from pymongo import MongoClient

from common import Singleton


class db(object):  # noqa
    __metaclass__ = Singleton

    def __init__(self):
        self.client = MongoClient()
        self.db = self.client.data
        # Collections:
        self.records = self.client.db.records
        self.pr_stats = self.client.db.pr_stats
        self.reviewers_pool = self.client.db.reviewers_pool

    def add_record(self, cases_properties, cases_checksum, action):
        db().records.insert_one({
            'cases_properties': cases_properties,
            'cases_checksum': cases_checksum,
            'action': {
                'checksum': action.hash,
                'name': action.class_name,
                'properties': action.properties
            }
        })

    def update_pr_stats(self, data):
        stat_key = {key: data[key] for key in ('organization', 'repository', 'number')}
        stat_exists = bool([s for s in self.pr_stats.find(stat_key)])
        if stat_exists:
            self.pr_stats.remove(stat_key)
        self.pr_stats.insert_one(data)

    def clear_db(self):
        # Deleting all the data in the db
        self.records.remove()
        self.pr_stats.remove()
        self.reviewers_pool.remove()
