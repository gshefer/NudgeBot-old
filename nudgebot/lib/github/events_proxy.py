import threading
import requests
import github
import time
import logging
from datetime import datetime

from common import Singleton, as_local_time
from nudgebot.lib.github import GithubEnv
from config import config
from nudgebot.db import db


logging.basicConfig()
logger = logging.getLogger('EventsProxyLogger')
logger.setLevel(logging.INFO)


class EventsProxy(threading.Thread):
    __metaclass__ = Singleton

    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self._last_check = None

    def run(self):
        logger.info('Starting events proxy.')
        while True:
            if (not self._last_check or ((datetime.now() - self._last_check).total_seconds() >
                                         config().config.events_proxy.check_timeout_seconds)):
                self._last_check = datetime.now()
                for repo in GithubEnv().repos:
                    logger.info('Searching for new event in repository "{}"'.format(repo.name))
                    for getter in ('get_events', 'get_issues_events'):
                        for event in getattr(repo, getter)():
                            is_this_new = (as_local_time(event.last_modified or event.created_at,
                                                         raise_if_native_time=False)
                                           < db().initialization_time)
                            is_this_me = event.actor.login == config().credentials.github.username
                            if (event.id in db().delivered_events or is_this_new or is_this_me):
                                break
                            logger.info('New event detected: id={}'.format(event.id))
                            if isinstance(event, github.IssueEvent.IssueEvent):
                                payload = event.raw_data
                            else:
                                payload = event.payload
                            # Fill some required fields that could be missing in the events API but
                            # coming with webhooks for some reason
                            payload['sender'] = {'login': event.actor.login}
                            payload['repository'] = payload.get('repository', {'name': repo.name})
                            requests.post('http://localhost:8080/webhooks', json=payload)
                            db().add_delivered_event(event.id)
            else:
                time.sleep(1)
