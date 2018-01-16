import pprint
from datetime import datetime

from pymongo import MongoClient

from common import Singleton
from bson import _ENCODERS as bson_encoders


class db(object):  # noqa
    __metaclass__ = Singleton
    bson_types = tuple(bson_encoders.keys())

    def __init__(self):
        self.client = MongoClient()
        self.db = self.client.data
        # Collections:
        self.records = self.client.db.records
        self.pr_stats = self.client.db.pr_stats
        self.reviewers_pool = self.client.db.reviewers_pool

    @classmethod
    def bson_encode(cls, node):
        """Verifying that all the object in the dict node are bson encodable.
        The once that are not, converted to str"""
        if isinstance(node, dict):
            result = {}
            for key, value in node.items():
                result[key] = cls.bson_encode(value)
        elif isinstance(node, (list, tuple)):
            result = []
            for item in node:
                result.append(cls.bson_encode(item))
        elif isinstance(node, cls.bson_types):
            result = node
        else:
            result = str(node)
        return result

    def add_record(self, cases_properties, cases_checksum, action):
        db().records.insert_one(self.bson_encode({
            'cases_properties': cases_properties,
            'cases_checksum': cases_checksum,
            'datetime': datetime.now(),
            'action': {
                'checksum': action.hash,
                'name': action.class_name,
                'properties': action.properties
            }
        }))

    def dump(self, filename=None):
        """Prettily dumping the DB content"""
        out = ''
        title = '_' * 40 + '{}' + '_' * 40 + '\n'
        for coll in ('records', 'pr_stats', 'reviewers_pool'):
            out += title.format(coll)
            docs = [r for r in getattr(self, coll).find()]
            if len(docs) == 1:
                docs = docs[0]
            out += pprint.pformat(docs, width=20) + '\n'
        if filename:
            with open(filename, 'w') as f:
                f.write(out)
        return out

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
