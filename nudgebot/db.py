from datetime import datetime

from pymongo import MongoClient

from common import Singleton


class db(object):  # noqa
    __metaclass__ = Singleton

    def __init__(self):
        self.client = MongoClient()
        self.db = self.client.data
        # Collections:
        self.sessions = self.client.db.sessions
        self.records = self.client.db.records
        self.stats = self.client.db.stats

    def new_session(self):
        old_sessions = [session['id'] for session in self.sessions.find()]
        data = {
            'id': (min(old_sessions)+1 if old_sessions else 0),
            'start_time': datetime.now()
        }
        self.sessions.insert_one(data)
        return data

    def add_record(self, session_id, cases_checksum, action, action_properties):
        db().records.insert_one({
            'session_id': session_id,
            'case_checksum': cases_checksum,
            'action': {
                'checksum': action.hash,
                'name': action.name,
                'properties': action_properties
            }
        })

    def add_stat(self, session_id, data):
        db().stats.insert_one({'session_id': session_id}, data)

    def clear_db(self):
        # Deleting all the data in the db
        self.records.remove()
        self.sessions.remove()
        self.stats.remove()
